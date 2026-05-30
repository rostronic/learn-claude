---
chapter: "2.3"
slug: "tool-errors"
title: "Structured error responses for tools"
module: "module-2-tools"
sequence: 7
references:
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "The is_error flag on tool_result; tool-execution vs. invalid-call errors; writing instructive error messages; server-tool errors"
  - title: "Give Claude custom tools (Agent SDK)"
    url: "https://code.claude.com/docs/en/agent-sdk/custom-tools"
    type: official_docs
    covers: "Handle errors: return isError instead of throwing (loop continues vs. stops); structuredContent; the MCP CallToolResult shape"
---

# Structured error responses for tools

## Overview

Tools fail — a network call times out, an input is malformed, a request violates a business rule, a caller lacks permission. How you *report* that failure back to the model decides whether the agent recovers gracefully or the whole run dies. CCAF Task Statement 2.2 is about getting this right: returning **structured error responses** so Claude can reason about what went wrong and what to do next.

The mechanism is small and specific. A tool result is a `tool_result` block, and it carries an optional `is_error` field: "`is_error` (optional): Set to `true` if the tool execution resulted in an error" ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). Setting that flag tells the model the call failed — so it can retry, try a different tool, or explain the failure to the user — instead of mistaking error text for a normal result. The discipline this lesson teaches is: **catch failures, return them as structured `is_error` results, and make the payload informative enough for Claude to act on.**

## How it works

### Return the error; never throw it

The single most important rule comes from the custom-tools guide, which contrasts the two ways a handler can fail ([Give Claude custom tools](https://code.claude.com/docs/en/agent-sdk/custom-tools)):

| What happens | Result |
|---|---|
| Handler throws an uncaught exception | "Agent loop stops. Claude never sees the error, and the `query` call fails." |
| Handler catches the error and returns `is_error: true` | "Agent loop continues. Claude sees the error as data and can retry, try a different tool, or explain the failure." |

So a tool handler must **catch its own exceptions and return them as error results** — an uncaught throw takes down the run. The docs' example wraps the work in `try/except` and, on failure, returns a result with `is_error: True` rather than letting the exception escape:

```python
import json
import httpx
from claude_agent_sdk import tool

@tool("fetch_data", "Fetch data from an API", {"endpoint": str})
async def fetch_data(args):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(args["endpoint"])
            if response.status_code != 200:
                # Return the failure as a tool result so Claude can react to it.
                return {
                    "content": [{"type": "text",
                                 "text": f"API error: {response.status_code} {response.reason_phrase}"}],
                    "is_error": True,
                }
            return {"content": [{"type": "text", "text": json.dumps(response.json())}]}
    except Exception as e:
        # Catching here keeps the agent loop alive. An uncaught exception
        # would end the whole query() call.
        return {"content": [{"type": "text", "text": f"Failed to fetch data: {str(e)}"}],
                "is_error": True}
```

On the raw Messages API the same idea is a `tool_result` block with `is_error: true` in your next `user` message ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)):

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "content": "ConnectionError: the weather service API is not available (HTTP 500)",
      "is_error": true
    }
  ]
}
```

Claude then folds that into its response — for example, telling the user the weather service is unavailable and to try again later.

### Make the message instructive

An error result is only useful if it tells Claude something it can act on. The docs are explicit: "Write instructive error messages. Instead of generic errors like `failed`, include what went wrong and what Claude should try next, e.g., `Rate limit exceeded. Retry after 60 seconds.` This gives Claude the context it needs to recover or adapt without guessing" ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). `"error"` or `"failed"` leaves Claude to guess; `"Rate limit exceeded. Retry after 60 seconds."` tells it exactly what to do.

### Categorize the error and flag retryability

Different failures call for different reactions, and Claude can only make that distinction if your result encodes it. This is the structured part of "structured error responses": each error carries a **category** and a **retryable** flag, not just free text. A useful, exam-aligned taxonomy:

| Category | Example | Retryable? |
|---|---|---|
| `transient` | network timeout, HTTP 503, rate limit | **yes** — the same call may succeed on retry |
| `validation` | malformed input, missing/invalid parameter | no — retrying the identical call fails identically |
| `business` | refund exceeds policy limit, action not allowed by rules | no — the request is well-formed but disallowed |
| `permission` | caller lacks access to the resource | no — retrying without new authorization changes nothing |

The retryable flag follows from the category: only `transient` failures are worth retrying as-is. Marking a validation or business error retryable invites Claude to loop on a call that can never succeed; marking a transient error non-retryable makes it give up on a blip it could have ridden out. (For a genuinely invalid *tool call* — missing required parameters — the docs note Claude "will retry 2-3 times with corrections" on an `is_error` result, and the durable fix is a more-detailed description or [strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use); see chapter 2.2.)

### Client tools vs. server tools

This discipline is for the tools *you* implement — client tools and custom MCP tools. For Anthropic's **server tools** (web search, code execution), you don't manage `is_error` yourself: "Claude will transparently handle these errors and attempt to provide an alternative response... Unlike client tools, you do not need to handle `is_error` results for server tools" ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). Know the boundary so you don't try to intercept failures Claude already manages.

## Worked example

The reusable piece is a **wrapper** that turns any tool handler into one that never throws and always returns a structured result — successes as normal results, failures as categorized `is_error` results. This is what you'll implement in the exercise:

```python
class TransientError(Exception): ...
class ValidationError(Exception): ...
class BusinessRuleError(Exception): ...
class PermissionDeniedError(Exception): ...

def classify_error(exc: Exception) -> tuple[str, bool]:
    """Return (category, retryable) for an exception."""
    if isinstance(exc, TransientError):
        return ("transient", True)
    if isinstance(exc, ValidationError):
        return ("validation", False)
    if isinstance(exc, BusinessRuleError):
        return ("business", False)
    if isinstance(exc, PermissionDeniedError):
        return ("permission", False)
    return ("unexpected", False)            # unknown failures are NOT blindly retried

def to_tool_result(tool_use_id, category, message, retryable) -> dict:
    """A structured error tool_result: is_error set, category + retryable in the payload."""
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "is_error": True,
        "content": {"error_category": category, "retryable": retryable, "message": message},
    }

def safe_invoke(handler, tool_use_id, args) -> dict:
    """Run a handler and ALWAYS return a tool_result — never raise."""
    try:
        result = handler(args)
    except Exception as exc:                 # catch everything; a throw would stop the loop
        category, retryable = classify_error(exc)
        return to_tool_result(tool_use_id, category, str(exc) or category, retryable)
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": result}  # success: no is_error
```

Walking through it:

- **`safe_invoke` never lets an exception escape.** The bare `except Exception` is deliberate — an uncaught throw would stop the agent loop, so the wrapper converts *every* failure into a returned result. This is the catch-don't-throw rule made concrete.
- **The success path carries no `is_error`.** A normal result must not be flagged as an error — doing so would tell Claude a successful call failed. Only failures set `is_error: True`.
- **The error payload is structured.** Category and retryable travel with the message, so Claude (and any orchestration around it) can branch on *which kind* of failure occurred, not parse prose.
- **Unknown exceptions default to non-retryable.** When you can't classify a failure, don't invite a retry loop on it — `("unexpected", False)` is the safe default.

## Anti-patterns & pitfalls

CCAF Task Statement 2.2 tempts you with error handling that looks fine but breaks the loop or starves Claude of what it needs:

1. **Letting the exception propagate.** A handler that raises instead of returning an `is_error` result stops the agent loop — "Claude never sees the error, and the `query` call fails." Catch failures and return them; never throw out of a tool handler.
2. **Generic, uninformative messages.** `"error"` or `"failed"` gives Claude nothing to act on. Write instructive messages that say what went wrong and what to try next (`"Rate limit exceeded. Retry after 60 seconds."`).
3. **Returning a failure as a normal (success) result.** Omitting `is_error` on a failure makes Claude treat error text as legitimate data and proceed on garbage. Flag every failure with `is_error: true`.
4. **Wrong retryability.** Marking a `validation`/`business`/`permission` error retryable sends Claude into a loop on a call that can never succeed; marking a `transient` error non-retryable makes it abandon a recoverable blip. Retry only the transient category.
5. **Hand-managing server-tool errors.** Trying to intercept `is_error` for web search or code execution — Claude already handles those transparently; this discipline is for the client/custom tools you implement.

The prescribed approach: **catch every failure inside the handler and return a structured `is_error` result whose message is instructive and whose category and retryable flag tell Claude how to react — and never throw, which would kill the loop.**

## Exam focus

This task statement shows up wherever tools touch unreliable systems:

- **Scenario 1 (Customer Support Resolution Agent)** — a refund tool that must distinguish "service is down, retry" (transient) from "amount exceeds policy" (business) and report each so the agent responds correctly.
- **Scenario 6 (Structured Data Extraction)** and **Scenario 3 (Multi-Agent Research System)** — tools hitting flaky external sources where transient failures should be retried and validation failures should not.

The reliable tell: the correct answer **catches the failure and returns a structured `is_error` result** with an actionable message and correct retryability. Distractors throw the exception (killing the loop), return a bare `"failed"`, or omit `is_error` so the failure masquerades as data.

## References & further reading

- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — the `is_error` field on `tool_result`, the tool-execution vs. invalid-call error cases, the "write instructive error messages" guidance, and why you don't manage `is_error` for server tools. The single best reference for this lesson.
- [Give Claude custom tools (Agent SDK)](https://code.claude.com/docs/en/agent-sdk/custom-tools) — the catch-don't-throw rule stated as a table (return `isError` so the loop continues, vs. throw and the loop stops), plus `structuredContent` for machine-readable results.

## Exam coverage

- **CCAF** — Domain 2 (Tool Design & MCP Integration), Task Statement 2.2: Implement structured error responses for MCP tools.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
