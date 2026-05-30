---
chapter: "7.8"
slug: "capstone-research-system"
title: "Capstone — Multi-Agent Research System"
module: "module-7-context-reliability"
sequence: 35
references:
  - title: "Agent SDK — Subagents"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Fresh context per subagent; only the final message returns to the parent; the prompt string is the only parent→child channel"
  - title: "Common workflows — Delegate research to subagents"
    url: "https://code.claude.com/docs/en/common-workflows"
    type: official_docs
    covers: "Delegating exploration so only findings return to the parent's context"
  - title: "Citations"
    url: "https://platform.claude.com/docs/en/build-with-claude/citations"
    type: official_docs
    covers: "Claim → source mapping with cited_text, document_index, location; guaranteed-valid pointers"
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "External-knowledge restriction, verify-with-citations, allow 'I don't know', report gaps"
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "is_error on tool_result; instructive 'what went wrong / what to try next' error messages"
---

# Capstone — Multi-Agent Research System

## Overview

This capstone is the place where five separate skills you've been building stop being independent and become one architecture. The scenario is the CCA-F's **Multi-Agent Research System**: a user asks a broad research question ("what's the state of solid-state battery commercialization?"), a **coordinator** decomposes it into focused sub-questions, fans those out to **research subagents** that each go read sources, and then synthesizes their findings into one cited answer — surfacing where sources disagreed and where nobody found anything.

It is tempting to treat this as "just a bigger agent loop." It isn't, and the difference is exactly what the exam tests. The moment you split work across subagents, three things that were free in a single loop become design decisions you have to get right:

- **Context isolation forces explicit hand-off.** Each subagent runs in its own context window; the coordinator's reasoning, the original query, the file paths it discovered — none of that is visible to a subagent unless the coordinator *writes it into the subagent's prompt* ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). The benefit (the parent's context stays clean) is inseparable from the obligation (you must pass everything the subagent needs, by hand).
- **Failures cross a boundary, and boundaries swallow failures.** Only a subagent's final message returns to the parent. If a subagent's retrieval times out and its final message doesn't *say so, and say which subagent it was*, the coordinator treats a non-answer as an answer and builds the synthesis on a hole.
- **The synthesis is an audit artifact, not a paragraph.** Folding N subagents' findings into one confident summary destroys the trail back to sources. The synthesis has to keep claim → source mapping, annotate conflicts instead of resolving them silently, and report coverage gaps.
- **Quality control can't be the writer grading its own homework.** Asking the synthesis agent "is this good?" gets you a yes. The prescribed move is an **independent review instance** — a fresh agent, in its own context, that never saw the synthesis being written.

This capstone ties together five task statements: subagent orchestration and context isolation (**1.2, 1.3**), error propagation with provenance across agents (**5.3**), provenance-preserving synthesis (**5.6**), and independent review (**4.6**). You won't write code here — you'll architect the system in a `design.md`, making each of those decisions explicitly and defending it. The lessons in this module each taught one piece; the exam scenario asks whether you can assemble them without dropping one.

## How it works

Walk the system as a concrete topology. A coordinator at the top, a fan-out of research subagents in the middle, a synthesis stage, and an independent review stage gating the output.

```
                         user research question
                                  │
                          ┌───────▼────────┐
                          │  COORDINATOR    │  decomposes question → sub-questions
                          │  (its own loop) │  spawns one subagent per sub-question
                          └───┬────┬────┬───┘
              prompt string   │    │    │   (the ONLY channel down)
              ┌───────────────┘    │    └───────────────┐
        ┌─────▼─────┐        ┌──────▼─────┐        ┌─────▼─────┐
        │ subagent A │        │ subagent B │        │ subagent C │   each: own context window
        │ "battery   │        │ "cost per  │        │ "regulatory│   own tool calls (hidden)
        │  chemistry"│        │  kWh trend"│        │  timeline" │   ONE final message back up
        └─────┬─────┘        └──────┬─────┘        └─────┬─────┘
              │ findings + provenance │ FAILED: timeout    │ findings + provenance
              │ (or structured error) │ (structured error) │
              └───────────────┬───────┴────────────────────┘
                          ┌───▼────────────────┐
                          │  COORDINATOR        │  collects findings + errors (with provenance)
                          │  SYNTHESIS          │  claim→source map, conflict annotation, gaps
                          └───┬─────────────────┘
                          ┌───▼─────────────────┐
                          │  INDEPENDENT REVIEW  │  fresh agent, own context, never saw the draft being written
                          │  (4.6)               │  checks: every claim sourced? conflicts kept? gaps reported?
                          └───┬─────────────────┘
                          revised / accepted answer
```

### (a) The coordinator loop and context isolation

The coordinator is an agentic loop (Task Statement 1.1's machinery) whose "tools" are *subagent invocations*. Delegating to a subagent is the prescribed way to keep the coordinator's own context clean: "Exploring a large codebase fills your context with file reads. Delegate the exploration so only the findings come back" ([Common workflows](https://code.claude.com/docs/en/common-workflows)). The same logic applies to research — each subagent reads a dozen sources, but only its distilled findings return; the coordinator never holds the raw source text, so it can coordinate many subagents without its context rotting.

That isolation is real and total. A subagent "runs in its own fresh conversation," and "intermediate tool calls and results stay inside the subagent; only its final message returns to the parent" ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). The consequence the exam keeps probing: **the coordinator's context does not flow downhill.** A subagent does not inherit the original user question, the coordinator's plan, the list of source paths it already found, or the decisions it made about scope. The only thing that crosses from parent to child is the **prompt string** the coordinator passes when it spawns the subagent.

### (b) Explicit context passing

Because the prompt string is the *only* channel down, the coordinator's most important job is constructing it. Each subagent's prompt must carry, explicitly:

- **The sub-question**, scoped narrowly ("Find the lowest reported $/kWh for solid-state cells in 2024–2025 and the source for each figure"), not the broad original.
- **The source pointers** the subagent should read — file paths, document indices, URLs the coordinator already located. The subagent can't see what the coordinator found; hand it the paths.
- **The output contract** — what shape the findings must come back in (e.g. "return a list of claims, each with the exact source span it rests on") so the synthesis stage can consume them. This is where you push the provenance and external-knowledge requirements *into* each subagent.
- **The decisions/constraints** that bound the work ("only use the provided documents, not your own knowledge" — the external-knowledge restriction, stated to each subagent because it won't inherit it ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations))).

If any of these lives only in the coordinator's head, the subagent never sees it. "The subagent will figure it out from context" is the trap — it has no shared context to figure it out from.

### (c) Error propagation with provenance across subagents

A subagent that fails returns one final message, just like one that succeeds. If that message is empty or success-shaped, the coordinator can't tell the difference — and it will fold a missing result into the synthesis as if it were data. So each subagent's output contract must include a **failure shape**, and the coordinator must collect failures as first-class results, each tagged with **which subagent** produced it:

```python
# A subagent's structured failure, carried in its final message
{"ok": False, "subagent": "cost-per-kwh", "error": "Vector store timed out after 30s", "transient": True}
```

The `subagent` field is the provenance — the *who failed*. Without it, a coordinator running five subagents gets "something broke" and can't retry the right branch, can't tell the user which part of the answer is missing, can't even log usefully. This mirrors the tool layer, where a failed tool returns `is_error: true` with a message that says "what went wrong and what Claude should try next" ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)) — the same discipline, lifted from the tool boundary to the agent boundary. The cardinal sin is **swallowing**: a `try/except` around a subagent call that returns `None` or `{}` on failure converts a loud, attributable failure into a silent hole in the synthesis. Subagent isolation means one subagent failing is a contained event — the coordinator records the attributed error and lets the other branches proceed, degrading the answer rather than collapsing the run ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).

### (d) Provenance-preserving synthesis

The coordinator's synthesis step folds the surviving subagents' findings into one answer, and it carries the contract from Task Statement 5.6. Mirror the Citations shape: every claim in the output travels with a non-empty list of source references — `document_index` (which source), `cited_text` (the exact span), and a location — and because those pointers are "guaranteed to contain valid pointers to the provided documents" ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)). A claim that doesn't resolve to a source a subagent actually returned is **dropped**, not emitted with a hedge — the external-knowledge restriction enforced structurally ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). Where two subagents' findings disagree, the synthesis **keeps both and annotates the resolution** (prefer the newer source, but record the loser) rather than silently picking one. And topics the coordinator asked about that no subagent could support are reported as explicit **coverage gaps** — the structural form of "allow Claude to say 'I don't know'" ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). The synthesis is an audit artifact: a reader can trace every claim to a subagent's source, see every disagreement, and see what's missing.

### (e) Quality via independent review

The last stage gates the output, and here the Anthropic position is sharp. The system must not ask the synthesis agent to grade its own work. An author reviewing its own draft shares the context — and the blind spots — that produced the draft; it rationalizes rather than catches. The prescribed move is an **independent review instance**: a fresh agent, in its own context window, that **never saw the synthesis being written** and receives only the finished artifact plus the checklist (every claim sourced? conflicts kept on the record? required topics either covered or listed as gaps?). Independence is the whole point — the reviewer's context isolation is what lets it catch what the writer can't see, the same isolation property that powers subagents ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Self-review is not a weaker version of this; on this exam it is the wrong answer.

### How the coordinator knows it's done

Termination is a deliberate decision, not "it stopped talking." The coordinator's loop ends when **every sub-question has resolved to either findings or a recorded structured error, the synthesis has been produced over the survivors, and the independent review has either accepted it or its revisions have been applied.** Outstanding sub-questions (a subagent still running, a transient failure inside its retry budget) mean *not done*. A clean termination state is: all branches accounted for (succeeded or attributed-failed), synthesis built, review passed. The coordinator does not declare success while a branch is still pending or a failure is unrecorded.

## Worked example

Trace one concrete run, end to end, to see the seams.

**Question.** "Summarize the state of solid-state battery commercialization: chemistry maturity, cost trend, and regulatory timeline."

**1. Decompose & spawn (coordinator, 1.2/1.3).** The coordinator splits the question into three sub-questions and spawns three subagents. Each spawn is a prompt string carrying the scoped sub-question, the source paths the coordinator located, the output contract (claims with source spans), and the external-knowledge restriction:

```
Subagent C (cost): "Find reported $/kWh figures for solid-state cells, 2023–2025.
Read ONLY these sources: [reports/cost-2024.pdf, reports/cost-2025.pdf].
Return a list of claims; each claim must include the exact source span and the source id.
Use only the provided documents, not your own knowledge."
```

Nothing about the *other* sub-questions, the user's phrasing, or the coordinator's plan is in that prompt — the subagent doesn't need it and won't inherit it.

**2. Fan-out runs in isolation.** Subagent A (chemistry) and C (cost) return findings, each a list of sourced claims. Subagent B (regulatory) hits a vector-store timeout. Its final message is not empty and not success-shaped — it's a structured, attributed error:

```python
{"ok": False, "subagent": "regulatory-timeline", "error": "Vector store timed out after 30s", "transient": True}
```

**3. Coordinator collects (5.3).** The coordinator gathers two successful findings and one structured error. Because the timeout is `transient` and within budget, it retries subagent B once; the retry also fails, so it records the attributed error and **moves on** — it does not abort A and C's work, and it does not thread a `None` for regulatory into the synthesis.

**4. Synthesis (5.6).** Over the two survivors, the coordinator produces an answer where every claim carries its source. The two cost sources disagree ($90/kWh vs $75/kWh); the synthesis keeps both, marks the newer one as resolved, and annotates the older as superseded. Regulatory timeline is listed as a **coverage gap** — asked for, not delivered, because the subagent failed — rather than silently omitted:

```python
{
  "items": [
    {"topic": "chemistry", "resolved": "Sulfide electrolytes lead pilot lines.",
     "provenance": [{"source_id": "chem-2025", "cited_text": "...sulfide-based cells in pilot production..."}]},
    {"topic": "cost", "resolved": "~$75/kWh (2025).",
     "provenance": [{"source_id": "cost-2025", "cited_text": "...$75 per kWh..."}],
     "conflicts": [{"statement": "~$90/kWh", "source_id": "cost-2024",
                    "annotation": "superseded by newer source cost-2025"}]},
  ],
  "coverage_gaps": ["regulatory-timeline"],
  "subagent_errors": [{"subagent": "regulatory-timeline", "error": "Vector store timed out after 30s"}],
}
```

**5. Independent review (4.6).** A fresh review agent — which never saw step 4 being assembled — receives only this artifact and a checklist: is every claim's `provenance` non-empty? Are conflicts kept rather than resolved silently? Is every required topic either covered or in `coverage_gaps`? It flags nothing structural here, so the answer is accepted. Had the writer dropped the cost conflict, an independent reviewer would catch it; the writer, sharing the writer's reasoning, would not.

**6. Termination.** All three branches are accounted for (two findings, one attributed failure), the synthesis is built over the survivors, and review passed. The coordinator is done — and the user sees an answer that is honest about what's missing.

This is the artifact your `design.md` describes: not the code, but the topology, the prompt contracts, the error shape, the synthesis guarantees, and the review architecture — with each decision named.

## Anti-patterns & pitfalls

Each of these is a way the scenario tempts you to collapse a multi-agent system back into something that loses information. All are wrong on this exam, not merely weaker.

1. **Assuming subagents share the coordinator's context.** Designing as if a subagent can "see" the original question, the plan, or the paths the coordinator found. It can't — only its prompt string crosses the boundary ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). The fix is to pass the sub-question, source paths, output contract, and constraints **explicitly** in every spawn. A design that says "the subagent uses the context" has no context to use.

2. **Swallowing subagent failures.** A `try/except` around a subagent call that returns `None`, `{}`, or an empty string on failure. This converts a loud, attributable failure into a silent hole the synthesis then builds on, and it destroys the provenance — *which* subagent failed — forever. **Never return a success-shaped value for a failed subagent.** Surface a structured error tagged with the failing subagent, exactly as the tool layer surfaces `is_error` with an instructive message ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

3. **Anonymous failures — one failure aborts the run.** Either propagating `{"error": "failed"}` with no `subagent` field, or re-raising a subagent's exception so the whole research run dies. The first is unactionable in a five-subagent system; the second throws away the blast-radius isolation subagents give you for free ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). One subagent failing is contained: record the attributed error and let the rest proceed.

4. **Blended, unsourced synthesis.** Folding everything into one fluent confident paragraph with no per-claim attribution. A reader can't verify any sentence and a fabrication is indistinguishable from a real finding. Anthropic's prescription is the opposite — claim → source mapping on every sentence ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)) — so **no claim is emitted without non-empty provenance**, conflicts are kept and annotated rather than silently resolved, and missing topics are reported as gaps rather than implied ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)).

5. **Self-review in place of independent review.** Asking the synthesis agent to grade its own output, or running a second "review" pass inside the *same* context that wrote the draft. It shares the writer's blind spots and rationalizes rather than catches. **Independent review instances beat self-review** — the reviewer must be a fresh agent in its own context that never saw the draft being written, receiving only the finished artifact and the checklist. This is the prescribed approach for Task Statement 4.6; "the model can check its own work" is the distractor.

The through-line for the whole capstone: a multi-agent system is trustworthy only when context is passed explicitly, failures stay visible and attributed, the synthesis stays auditable, and an *independent* agent gates the output. Any design that quietly relies on shared context, swallows a failure, blends sources, or self-grades is the wrong answer.

## Exam focus

This is the assembly test. Where the single-topic chapters each ask "do you know mechanism X," the Multi-Agent Research System scenario asks "can you wire X, Y, and Z together without dropping one." Expect questions that pose the *whole* topology and tempt you with a single seductive shortcut:

- A subagent "will infer the scope from context" — wrong, because context doesn't flow downhill; pass it in the prompt.
- A `try/except` that "handles the failure gracefully" by returning a default — wrong, because that's swallowing; surface an attributed structured error.
- A synthesis that "produces a clean, confident summary" — wrong, because it dropped the provenance, the conflict, and the gap.
- A review step where "the agent double-checks its own answer" — wrong, because independent review beats self-review.

The correct answer is always the one that keeps context explicit, failures attributed and contained, synthesis auditable, and review independent. Domain 5 (Context Management & Reliability) supplies the synthesis and propagation pieces; Domain 1 supplies the orchestration; Domain 4 supplies the independent-review discipline.

## References & further reading

- [Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — fresh context per subagent, only the final message returns to the parent, and the prompt string as the sole parent→child channel. The basis for both the explicit-context-passing requirement and the failure-containment benefit.
- [Common workflows — Delegate research to subagents](https://code.claude.com/docs/en/common-workflows) — the recipe for delegating exploration so only the findings return to the parent's context; the coordinator/subagent fan-out this capstone builds.
- [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) — the `claim → source` pointer (`document_index`, `cited_text`, location) with guaranteed-valid references; the shape the synthesis's provenance mirrors.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — external-knowledge restriction, verify-with-citations, "allow Claude to say 'I don't know'"; the basis for dropping unsourced claims and reporting coverage gaps.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — `is_error` and instructive error messages; the tool-boundary version of attributed error propagation across subagents.

## Exam coverage

- **CCAF** — Scenario 3: Multi-Agent Research System. This capstone ties together Task Statements 1.2, 1.3, 5.3, 5.6, and 4.6.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
