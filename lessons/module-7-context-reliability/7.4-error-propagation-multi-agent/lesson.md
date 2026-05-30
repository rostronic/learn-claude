---
chapter: "7.4"
slug: "error-propagation-multi-agent"
title: "Error propagation across multi-agent systems"
module: "module-7-context-reliability"
sequence: 31
references:
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "is_error on tool_result; writing instructive 'what went wrong / what to try next' error messages"
  - title: "Agent SDK — Subagents"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Fresh context per subagent; only the final message returns to the parent; explicit parent↔child channel"
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs
    covers: "The loop that consumes subagent results; stop_reason; how a failed step re-enters the loop"
---

# Error propagation across multi-agent systems

## Overview

A multi-agent system is a set of loops that hand work to each other: a coordinator delegates to subagents, each subagent runs its own loop, and the coordinator stitches the results together. The hard part isn't the happy path — it's what happens when a subagent fails. Does the coordinator find out? Does it find out *which* subagent failed and *why*? Or does a silent `None` slip downstream and corrupt the final answer?

Task Statement 5.3 is "**Implement error propagation strategies across multi-agent systems**." The skill it tests is making failures **visible, attributable, and recoverable** as they cross agent boundaries — instead of swallowed, anonymous, and fatal.

The reason this is genuinely hard with Claude subagents is a property of how they're isolated. "Each subagent runs in its own fresh conversation," and crucially "intermediate tool calls and results stay inside the subagent; only its final message returns to the parent" ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). The parent does not see the subagent's stack trace, its retries, or the tool error that derailed it. It sees one message. So if that final message doesn't *say* "I failed, here's what broke," the failure is invisible — the parent will treat a non-answer as an answer. Error propagation is the discipline of making sure the failure is in that final message, in a form the parent can act on.

## How it works

There are three moving parts: a **structured error object** that carries provenance, the **boundary** where a failure surfaces, and the **policy** the coordinator applies (retry / fall back / fail cleanly).

### Structured errors that carry provenance

An error crossing an agent boundary must answer two questions: *who failed* and *what to do about it*. "Provenance" is the *who* — the agent or stage that produced the failure. Without it, a coordinator running five subagents gets "something failed" and can't route, retry, or report. So errors are **structured objects**, not bare strings or exceptions that vanish at the boundary:

```python
{
    "ok": False,
    "stage": "retrieval",          # PROVENANCE: which agent/stage failed
    "error": "Vector store timed out after 30s",
    "transient": True,             # is a retry plausibly worth it?
}
```

This mirrors how the model layer itself surfaces tool failures. When a tool a subagent calls fails, you return its `tool_result` with `is_error: true`, and "Claude will then incorporate this error into its response" ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). The `is_error` flag is exactly a structured "this didn't succeed" signal at the tool boundary; our dict is the same idea at the *agent* boundary. The error string is the `error` field; the recoverability hint is `transient`.

### Instructive messages, not generic ones

The content of `error` matters as much as its presence. The docs are explicit: write messages that "include what went wrong and what Claude should try next," and the example they give is the gold standard — `"Rate limit exceeded. Retry after 60 seconds."` rather than a bare `"failed"` ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). A generic `"error"` tells the coordinator (whether it's Claude or your code) nothing it can act on. An instructive message tells it the failure *class* and the *next move*. This is the difference between an error a system can recover from and one it can only log.

### The boundary: surface, never swallow

Because only the final message crosses back to the parent, the boundary code has exactly one job: **put the failure in that message.** The cardinal sin is *swallowing* — catching a failure and returning a success-shaped value anyway:

```python
# WRONG — swallows the failure
def run_stage(fn, value):
    try:
        return fn(value)
    except Exception:
        return None        # downstream sees None, treats it as a valid result
```

That `None` is poison. The next stage receives it as if it were real data; the final answer is built on a hole; and the provenance — *which* stage produced the hole — is gone forever. The fix is to convert the failure into a structured error and **stop threading a missing value forward**.

### The policy: retry transient, fall back / fail cleanly on hard

Not every failure deserves the same response. The `transient` flag drives a policy the coordinator applies. Subagent results re-enter the coordinator's loop ([Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)); the retry / substitute / stop policy below is this lesson's own design layered on top of that loop, not something the agent-loop doc prescribes:

- **Transient** (timeout, rate limit, a flaky network read): **retry** a bounded number of times. These often succeed on the second attempt; giving up immediately wastes a recoverable result.
- **Hard / non-transient** (bad input, a contract violation, a 4xx that won't change on retry): retrying just burns turns. **Fall back** to a degraded-but-valid result if one exists, or **fail cleanly** — record the structured error and stop — if it doesn't.

"Fail cleanly" is the load-bearing phrase. It does *not* mean raise and crash the process; it means terminate this branch of work in a defined state, with the error recorded, without taking down the rest of the system.

### Isolation: one failure must not crash the whole system

This is where the multi-agent shape pays off. Subagent isolation isn't only a context-window benefit — it's a **blast-radius** benefit. Each subagent runs in its own context, so a subagent that derails doesn't corrupt the coordinator's reasoning or its siblings' work; the coordinator can let that one branch fail and keep the others ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Your propagation code has to honor that: a single failing stage produces a structured error and is contained — it does not raise out and abort every other stage. The system degrades; it does not collapse.

## Worked example

Here's a sequential pipeline coordinator that puts all three parts together. Each stage is a `(name, fn)` pair; `fn(input)` returns a result dict `{"ok": bool, "value"?, "error"?, "transient"?}`. The coordinator threads the previous stage's `value` forward, retries transient failures, and on a hard failure stops downstream work and records a structured, attributed error — without ever raising. This is the shape the exercise grades.

```python
def run_pipeline(stages, initial_input, max_retries=1):
    results = []
    errors = []
    current = initial_input

    for name, fn in stages:
        outcome = _run_stage_with_retries(name, fn, current, max_retries)

        if outcome["ok"]:
            current = outcome["value"]
            results.append({"stage": name, "value": current})
            continue

        # Failure: record a STRUCTURED, ATTRIBUTED error and STOP.
        # Do NOT thread the (missing) value forward to the next stage.
        errors.append({
            "stage": name,                      # provenance
            "error": outcome.get("error", "unknown error"),
            "recoverable": bool(outcome.get("transient", False)),
        })
        return {"status": "failed", "results": results, "errors": errors}

    return {"status": "ok", "results": results, "errors": errors}


def _run_stage_with_retries(name, fn, value, max_retries):
    attempt = 0
    while True:
        outcome = fn(value)
        if outcome.get("ok"):
            return outcome
        # Retry only transient failures, and only up to the budget.
        if outcome.get("transient") and attempt < max_retries:
            attempt += 1
            continue
        return outcome
```

Walking through it:

- **A successful stage's `value` becomes the next stage's input.** A *failed* stage's value is never threaded forward — the `continue` only runs on `ok`, and the failure branch `return`s. The missing value cannot reach the next stage, so it cannot corrupt it.
- **Provenance is captured at the boundary.** The `errors` entry carries `stage` — the name of the agent/stage that failed — so the caller knows exactly who broke, the analog of `is_error` plus an instructive message at the tool layer.
- **Transient failures retry; hard failures don't.** `_run_stage_with_retries` loops only while the failure is `transient` and the budget allows; a non-transient failure returns on the first attempt. Retrying a hard error would just waste work.
- **It never raises.** On any failure it returns a well-formed aggregate `{"status": "failed", "results": [...], "errors": [...]}`. The coordinator's caller always gets a structured answer it can inspect — one subagent's failure is contained, not fatal.

A caller then reads the aggregate and decides what to surface — exactly the "incorporate this error into its response" behavior, lifted to the coordinator level:

```python
report = run_pipeline(stages, raw_input, max_retries=2)
if report["status"] == "failed":
    failed = report["errors"][0]
    log.warning("pipeline stopped at %s: %s", failed["stage"], failed["error"])
```

## Anti-patterns & pitfalls

The exam tempts you with four wrong moves. Each one is a way of *losing* the failure.

1. **Swallowing the error — returning `None`/`{}` as if it succeeded.** This is the worst one. A `try/except` that returns `None` on failure converts a loud failure into a silent corruption: downstream stages consume the `None` as real data and the final answer is quietly wrong, with no trace of where it went bad. **Never return a success-shaped value for a failed step.** Convert the failure to a structured error and stop threading a value forward. The CCA-F treats swallowing as the canonical Domain 5 anti-pattern — it's wrong, not "less ideal."

2. **Anonymous errors — no provenance.** Propagating `{"ok": False, "error": "failed"}` with no `stage` tells the coordinator something broke but not *what*. In a five-subagent system that's unactionable: you can't retry the right branch, can't report which capability is down, can't even write a useful log line. **Every error that crosses a boundary carries the failing agent/stage.**

3. **Generic, non-instructive messages.** `"error"` or `"something went wrong"` is barely better than no message. The docs prescribe messages that say *what went wrong and what to try next*, e.g. `"Rate limit exceeded. Retry after 60 seconds."` ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). A generic message strips out the one thing that makes an error recoverable: the class of failure and the next move.

4. **Letting one failure crash the whole system.** Re-raising a subagent's exception out of the coordinator so the entire run aborts throws away the isolation that subagents give you for free ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). One subagent failing is a contained, expected event; the prescribed response is to record it and let the rest of the system proceed or degrade — **not** to take everything down. "Fail cleanly" means stop *this branch* in a defined state, not crash the process.

A related pitfall: **retrying hard errors.** A 400-class failure (bad input, invalid contract) won't change on retry; looping on it just burns turns and latency. Retry is for *transient* failures only — gate it on the `transient` flag, not on "did it fail."

## Exam focus

Error propagation is a Domain 5 (Context Management & Reliability) skill and shows up wherever the exam describes a system with more than one agent:

- **Multi-Agent Research System** — a coordinator fans work out to research subagents; the question is what the coordinator does when one subagent's retrieval times out. The right answer surfaces a structured, attributed error and contains it; distractors swallow it or abort the run.
- **Customer Support Resolution Agent** — a tool or subagent the support agent depends on fails mid-resolution. The prescribed move is an `is_error` result with an instructive message so the agent can recover or escalate, not a generic failure.

Expect distractors that *look* defensive but lose information: broad `try/except` that returns a default, "log it and continue with `None`," single-message errors with no provenance, retry-everything loops, and re-raise-and-abort. The correct answer is always the one that keeps the failure **visible, attributed, and contained**.

## References & further reading

- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — the `is_error` flag on a `tool_result` and the rule to write instructive messages ("what went wrong and what to try next", e.g. "Rate limit exceeded. Retry after 60 seconds."). This is the tool-boundary version of everything in this lesson.
- [Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — why only a subagent's final message returns to the parent, and why that isolation both *requires* explicit error surfacing and *gives* you failure containment.
- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — the coordinator loop that consumes subagent results and applies the retry / fall-back / fail-cleanly policy.

## Exam coverage

- **CCAF** — Domain 5 (Context Management & Reliability), Task Statement 5.3: Implement error propagation strategies across multi-agent systems.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
