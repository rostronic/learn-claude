# Capstone — Multi-Agent Research System — exercise

## What you're building

This is a **design exercise**, not a coding one. You'll architect the Multi-Agent Research System from the lesson and write it up as a `design.md`. No starter code, no tests — the deliverable is the architecture and the decisions behind it, defended against the anti-patterns the scenario tempts you with.

The scenario: a user asks a broad research question. A **coordinator** decomposes it into sub-questions, fans them out to **research subagents** (each in its own context window), then synthesizes their findings into one cited answer and gates that answer through review before returning it.

Write your design to:

```
~/learn-claude-work/7.8/design.md
```

(Create the directory if it doesn't exist: `mkdir -p ~/learn-claude-work/7.8`.)

## What your design.md must cover

Address all five sections. Be concrete — name the subagents, show the prompt contract, show the error shape and the synthesis shape. A reviewer should be able to read your design and know exactly what crosses each boundary.

1. **Coordinator / subagent topology + per-subagent prompt.** Pick a concrete research question and decompose it into sub-questions, one per subagent. Draw or describe the topology (coordinator → fan-out → synthesis → review). For each subagent, specify **what its prompt string contains** — remember the prompt is the *only* channel from coordinator to subagent. Spell out the scoped sub-question, the source pointers it should read, the output contract for its findings, and any constraints (e.g. external-knowledge restriction). State explicitly why nothing else (the original question, the coordinator's plan) is available to the subagent unless you pass it.

2. **Error propagation with provenance.** Define the **failure shape** a subagent returns in its final message, including the field that names *which* subagent failed. Describe how the coordinator collects failures alongside successes, how it decides whether to retry (transient vs. hard), and what it does when a branch fails permanently. State the rule that a failed subagent's result is never threaded into the synthesis as if it were data.

3. **Provenance-preserving synthesis.** Show the shape of the synthesized answer. Every claim must carry a non-empty source reference (claim → source mapping). Specify how conflicts between subagents are handled (kept and annotated, not silently resolved), how unsourced claims are treated (dropped, not hedged), and how topics no subagent could support are surfaced (explicit coverage gaps).

4. **Independent-review architecture.** Describe the review stage. Make clear it is an **independent review instance** — a fresh agent, in its own context, that never saw the synthesis being written — and state what it receives (the finished artifact + a checklist) and what it checks. Explain why this beats having the synthesis agent review its own work.

5. **How the coordinator knows it's done.** Define the termination condition precisely: what state must every branch be in, what must be true of the synthesis and the review, and what "not done" looks like (a pending branch, an unrecorded failure, a transient retry still in budget).

## What your design must NOT do

The rubric grades these directly as anti-patterns. Avoid them:

- **Do NOT rely on subagents sharing the coordinator's context.** Don't write "the subagent already knows the question / sees the plan." Context doesn't flow downhill; pass it in the prompt.
- **Do NOT swallow subagent failures.** No `try/except` that returns `None`/`{}`/empty on failure, no anonymous `{"error": "failed"}`, no re-raise that aborts the whole run. Surface a structured, attributed error and contain it.
- **Do NOT use self-review in place of independent review.** Don't have the synthesis agent grade its own output, and don't run the "review" inside the same context that wrote the draft.

## How to submit

Save your `design.md` to `~/learn-claude-work/7.8/design.md`, then run `/verify 7.8` and I'll grade it against the rubric.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't; the worked example is the shape your design describes.
- [Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — fresh context per subagent; the prompt string is the only parent→child channel.
- [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) — the claim → source shape your synthesis mirrors.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — external-knowledge restriction and coverage-gap reporting.
