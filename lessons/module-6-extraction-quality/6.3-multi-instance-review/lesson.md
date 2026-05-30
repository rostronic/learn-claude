---
chapter: "6.3"
slug: "multi-instance-review"
title: "Multi-instance & multi-pass review architectures"
module: "module-6-extraction-quality"
sequence: 26
references:
  - title: "Create custom subagents"
    url: "https://code.claude.com/docs/en/sub-agents"
    type: official_docs
    covers: "Each subagent runs in its own context window and works independently — the mechanism for an independent reviewer"
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "Forcing a findings tool so each review pass returns structured findings (with confidence/detected_pattern)"
  - title: "Subagents in the Agent SDK"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Spawning isolated subagents programmatically, each with its own context — for parallel independent passes"
---

# Multi-instance & multi-pass review architectures

## Overview

When Claude generates code (or extracts data, or writes a plan) and you want a *quality check* on that output, the tempting move is to ask the same conversation to review its own work: "now look back over what you just wrote and find any bugs." It feels efficient — the model already has all the context. It is also the wrong architecture, and the exam is unambiguous about why.

A model that just generated something **retains the reasoning context from generation**, which makes it "less likely to question its own decisions in the same session." It already convinced itself the code was right; asking it to re-examine the same reasoning rarely surfaces the flaw. The Anthropic-prescribed approach is a **second, independent instance** — a reviewer with *no prior reasoning context* — which is "more effective at catching subtle issues than self-review instructions or extended thinking." This is the Domain 4 stance, and the correct answer rewards it directly: independent review beats self-review, full stop.

The companion idea is **multi-pass review** for large changes. A single pass asked to review fourteen files at once suffers *attention dilution*: thorough on some files, superficial on others, and prone to *contradictory* findings (flagging a pattern in one file while approving identical code in another). The fix is to split the work — focused per-file passes for local issues, plus a separate integration pass for cross-file data flow.

## How it works

### Independent review instances

An independent reviewer is just a Claude instance that receives **only the artifact under review** — not the conversation that produced it. The "independence" is structural: a fresh context window with no generation transcript in it. In Claude Code, that's exactly what a subagent gives you — "each subagent runs in its own context window... works independently and returns results" ([Create custom subagents](https://code.claude.com/docs/en/sub-agents)); the docs even walk through building a `code-reviewer` subagent for this. Programmatically, you get the same isolation by starting a brand-new Messages conversation, or by spawning an isolated subagent through the Agent SDK ([Subagents in the Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents)).

What makes it independent is what you *don't* pass in. The reviewer's `messages` contain the code and a review instruction — and no assistant turns from the generator:

```python
def independent_review(client, code, review_tool):
    # Fresh context: ONLY the code under review. None of the generator's
    # reasoning or conversation is threaded in — that's what makes it independent.
    messages = [{
        "role": "user",
        "content": f"Independently review this code for issues. "
                   f"Call {review_tool['name']} with your findings.\n\n{code}",
    }]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        tools=[review_tool],
        tool_choice={"type": "tool", "name": review_tool["name"]},  # structured findings
        messages=messages,
    )
    block = next(b for b in response.content if b.type == "tool_use")
    return block.input["findings"]
```

Note the reviewer returns **structured findings** via a forced tool call ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)), not prose — which sets up the confidence routing below.

### Multi-pass review

For a change spanning many files, you run **per-file passes** for local issues, then a **separate integration pass** for cross-file concerns. Each per-file pass sees one file and isn't distracted by the others; the integration pass sees all of them precisely to reason about how they interact:

```python
def multi_pass_review(client, files, review_tool):
    findings = []
    for path, contents in files.items():                 # local passes, one per file
        findings += _review_pass(client,
            f"Review ONLY {path} for local issues.\n\n{contents}", review_tool)

    combined = "\n\n".join(f"### {p}\n{c}" for p, c in files.items())
    findings += _review_pass(client,                      # one integration pass
        f"Review these files together for cross-file data-flow issues.\n\n{combined}",
        review_tool)
    return findings
```

`N` files cost `N + 1` passes. The split is the point: it's what eliminates the "detailed on some files, superficial on others, contradictory across files" failure mode of one giant pass.

### Confidence-calibrated routing

Because each finding comes back structured, you can have the reviewer **self-report confidence** alongside each finding and route accordingly — high-confidence findings act automatically, low-confidence ones go to a human. This is "running verification passes where the model self-reports confidence alongside each finding to enable calibrated review routing":

```python
def route_by_confidence(findings, threshold=0.8):
    auto = [f for f in findings if f["confidence"] >= threshold]
    human_review = [f for f in findings if f["confidence"] < threshold]
    return {"auto": auto, "human_review": human_review}
```

One more structured-findings payoff the exam names: give each finding a **`detected_pattern`** — the code construct that triggered it. When developers later dismiss findings, the `detected_pattern` field lets you analyze *which patterns* produce false positives systematically, so you can tune the noisy rules instead of guessing.

## Worked example

A two-stage architecture: generate, then review with an independent instance, then route by confidence. The generator and the reviewer are deliberately *different conversations* — the reviewer never sees the generator's reasoning.

```python
def generate_and_review(client, task, review_tool):
    # Stage 1 — generation (its own conversation/context).
    gen = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=2048,
        messages=[{"role": "user", "content": task}],
    )
    code = gen.content[0].text

    # Stage 2 — review by a FRESH instance. We pass `code`, NOT `gen`'s messages.
    findings = independent_review(client, code, review_tool)

    # Stage 3 — route on self-reported confidence.
    routed = route_by_confidence(findings)
    return code, routed
```

Walking through it:

- **Two separate conversations.** Generation happens in one `messages` thread; review happens in another. The only thing that crosses the boundary is the *artifact* (`code`) — never the reasoning. If you instead appended "now review yourself" to `gen`'s messages, you'd be doing self-review, and the reviewer would carry the very bias that hid the bug.
- **The reviewer is forced to return findings,** so `route_by_confidence` has structured data to work with.
- **For a multi-file change,** swap `independent_review(client, code, ...)` for `multi_pass_review(client, files, ...)` — same independence, now split across focused passes.

## Anti-patterns & pitfalls

Task Statement 4.6 makes each of these a distractor — and several are the *tempting, plausible* option:

1. **Self-review in the same session.** Asking the generating instance to critique its own output ("now check your work"). It keeps the reasoning that produced the bug, so it's least likely to catch it. **Independent instances beat self-review** — this is the prescribed answer, not a preference. Self-review instructions are explicitly weaker.
2. **Reaching for extended thinking instead of a second instance.** "Let the model think harder about its own output." More thinking in the *same* context still doesn't shed the generation bias; the guide ranks an independent instance above both self-review instructions *and* extended thinking for catching subtle issues. Don't substitute more compute in one head for a genuinely separate one.
3. **One giant single-pass review of a large multi-file change.** Reviewing fourteen files in one prompt invites attention dilution and contradictory findings. Split into per-file passes plus an integration pass.
4. **A "bigger context window" as the fix for dilution.** "Use a higher-tier model with a larger context so all files fit." The problem isn't that the files don't fit — it's attention spread thin across them in a single pass. A larger window doesn't focus attention; restructuring into passes does.
5. **Requiring humans to pre-split large PRs** so the automated review can cope. That pushes the tool's limitation onto developers. The reviewer should restructure *its own* analysis into passes, not mandate smaller PRs.
6. **Naive multi-run voting as a substitute for structure.** Running the same full-PR review three times and keeping findings that appear in ≥2 runs. It's still the same diluted single-pass, just repeated and more expensive; it doesn't fix attention dilution the way per-file + integration passes do.

The throughline: **quality comes from independence and focus** — a separate instance with no generation context, and large reviews split into per-file plus integration passes. Self-review, extended thinking, bigger windows, and repeated full-PR runs are the distractors that *look* like quality without delivering it.

## Exam focus

This task statement anchors **Scenario 2 (Code Generation)** and **Scenario 5 (CI)**, wherever generated code or a PR needs reviewing. The two reliable distractor families: "have the model review its own work / think harder" (defeated by *independent instance*) and "review all files in one pass / use a bigger model" (defeated by *per-file + integration passes*). The correct answer is always the one that introduces an independent reviewer and/or splits a large review into focused passes; confidence self-reporting then routes findings between automation and humans.

## References & further reading

- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — subagents each run in their own context window and work independently; the canonical mechanism for an independent reviewer (with a `code-reviewer` walkthrough).
- [Subagents in the Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — spawning isolated subagents programmatically, each with a fresh context, for parallel independent passes.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — forcing a findings tool so each review pass returns structured findings you can route by confidence and analyze by `detected_pattern`.

## Exam coverage

- **CCAF** — Domain 4 (Prompt Engineering & Structured Output), Task Statement 4.6: Design multi-instance and multi-pass review architectures.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
