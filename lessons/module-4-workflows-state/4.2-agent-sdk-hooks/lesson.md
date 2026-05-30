---
chapter: "4.2"
slug: "agent-sdk-hooks"
title: "Agent SDK hooks for tool interception & normalization"
module: "module-4-workflows-state"
sequence: 13
references:
  - title: "Agent SDK — Intercept and control agent behavior with hooks"
    url: "https://code.claude.com/docs/en/agent-sdk/hooks"
    type: official_docs
    covers: "Hook events, HookMatcher registration, PreToolUse/PostToolUse, permissionDecision, updatedInput, updatedToolOutput, deny precedence"
  - title: "Claude Code — Hooks reference"
    url: "https://code.claude.com/docs/en/hooks"
    type: official_docs
    covers: "The full hook JSON input/output schema and matcher patterns shared by SDK callback hooks"
---

# Agent SDK hooks for tool interception & normalization

## Overview

The previous chapter used a `PreToolUse` gate to enforce a workflow rule. This chapter is about the mechanism that made it possible: **hooks** — callback functions the Agent SDK runs at fixed points in an agent's execution, "like a tool being called, a session starting, or execution stopping" ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). A hook is your code, on the critical path, with the authority to block an operation, rewrite its inputs, or rewrite its outputs before the model ever sees them.

That makes hooks the **deterministic** layer of an agent. Anything you need to be *guaranteed* — a path can never be written, a payload is always shaped a certain way, every tool call is audited — belongs in a hook, not in the prompt. The model's behavior is probabilistic; a hook is code that runs every time. This lesson focuses on the two tool hooks you'll reach for most: `PreToolUse` (intercept a call before it runs — block or modify its input) and `PostToolUse` (intercept a result after it runs — normalize or annotate it).

## How it works

You register hooks in the `hooks` option of `ClaudeAgentOptions`. The key is the **event name**; the value is a list of `HookMatcher`s, each pairing an optional `matcher` regex with one or more callbacks ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)):

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env_files])],
    }
)
```

A few mechanics decide whether your hook does what you intend:

- **Matchers filter by *tool name* only.** The `matcher` regex is tested against the tool name — `"Write|Edit"`, `"Bash"`, `"^mcp__"` for MCP tools ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). It does **not** see arguments. To act on a *file path* or any other argument, you must inspect `tool_input` inside the callback. This is the single most common hook bug.
- **The callback signature is `(input_data, tool_use_id, context)`.** `input_data` is a dict; every event shares `session_id`, `cwd`, and `hook_event_name`, and `PreToolUse` adds `tool_name` and `tool_input` ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). `tool_use_id` correlates a `PreToolUse` with its matching `PostToolUse`.
- **The return value is a decision dict.** Return `{}` to allow the operation unchanged. To influence it, return a `hookSpecificOutput` whose fields depend on the event (below). Top-level fields like `systemMessage` and `continue` work on every event.
- **`deny` wins.** Across all hooks and permission rules, the precedence is `deny` > `defer` > `ask` > `allow` — "if any hook returns `deny`, the operation is blocked regardless of other hooks" ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). Multiple hooks on one event run in parallel, so write each to stand alone.

### PreToolUse: block or modify a call

For `PreToolUse`, `hookSpecificOutput` carries `permissionDecision` (`"allow"`, `"deny"`, `"ask"`, or `"defer"`), `permissionDecisionReason`, and `updatedInput` ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). To **block**, return `permissionDecision: "deny"` with a reason. To **modify** the call's arguments, return `updatedInput` — but with one rule the docs call out twice: "you must also include `permissionDecision: 'allow'`" (or `'ask'`) for the modified input to take effect, and "always return a new object rather than mutating the original `tool_input`" ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). An `updatedInput` without an `allow` is silently dropped.

```python
async def protect_env_files(input_data, tool_use_id, context):
    file_path = input_data["tool_input"].get("file_path", "")
    if file_path.split("/")[-1] == ".env":            # inspect the ARGUMENT, not the matcher
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "deny",
                "permissionDecisionReason": "Cannot modify .env files",
            }
        }
    return {}
```

### PostToolUse: normalize or annotate a result

`PostToolUse` fires after a tool returns; its `input_data` carries the tool's result in a `tool_response` field ([Hooks reference](https://code.claude.com/docs/en/hooks)). Its `hookSpecificOutput` can set `additionalContext` to *append* information to the tool result, or `updatedToolOutput` to *replace* the tool's output entirely "before Claude sees it" ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). That replacement channel is your **data-normalization** seam: a third-party tool or MCP server might return inconsistent keys, missing fields, or the wrong units; a `PostToolUse` hook coerces every result into one canonical shape so the model — and the rest of your code — only ever sees the clean version. Because it runs every time, the guarantee is structural, not a hope that the upstream tool behaves.

## Worked example

Two hooks on one agent: a `PreToolUse` guard that blocks writes to `.env`, and a `PostToolUse` normalizer that canonicalizes a weather tool's payload. Real `claude_agent_sdk` wiring, with `ClaudeSDKClient`:

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher


async def protect_env_files(input_data, tool_use_id, context):
    file_path = input_data["tool_input"].get("file_path", "")
    if file_path.split("/")[-1] == ".env":
        return {"hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "deny",
            "permissionDecisionReason": "Cannot modify .env files",
        }}
    return {}


async def normalize_weather(input_data, tool_use_id, context):
    response = input_data.get("tool_response", {})
    canonical = {k.lower(): v for k, v in response.items()}
    canonical.setdefault("units", "fahrenheit")
    if canonical == response:
        return {}                      # already canonical — nothing to do
    return {"hookSpecificOutput": {
        "hookEventName": input_data["hook_event_name"],
        "updatedToolOutput": canonical,
    }}


async def main():
    options = ClaudeAgentOptions(hooks={
        "PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env_files])],
        "PostToolUse": [HookMatcher(matcher="get_weather", hooks=[normalize_weather])],
    })
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Update the config and report the weather")
        async for message in client.receive_response():
            print(message)


asyncio.run(main())
```

What to notice:

- **`protect_env_files` reads `tool_input["file_path"]`,** even though the matcher already narrowed to `Write|Edit`. The matcher can't see the path; only the callback can. Drop that check and you'd block *all* writes, not just `.env`.
- **`normalize_weather` returns `{}` when the payload is already canonical.** An idempotent hook avoids pointless rewrites and is easy to reason about — "change only if needed."
- **`updatedToolOutput` replaces what the model sees.** Downstream reasoning operates on `{"temperature": ..., "units": "fahrenheit"}` regardless of how the raw tool capitalized its keys.

The exercise has you implement three callbacks of this exact shape — a `.env` guard, a normalizer, and an input-rewriting redirect — and test them as pure functions.

## Anti-patterns & pitfalls

1. **Expecting the matcher to filter by argument.** `HookMatcher(matcher="/etc")` does nothing useful — matchers match the *tool name*, never a path or other argument ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). To filter by file path you must read `tool_input.file_path` inside the callback. A matcher of `.env` matches a *tool literally named* `.env`, not a write whose path ends in `.env`.

2. **Returning `updatedInput` without `permissionDecision: "allow"`, or mutating `tool_input` in place.** The SDK ignores a modified input unless you also allow it, and mutating the original dict instead of returning a new one is explicitly warned against ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). Both produce the same baffling symptom: "my hook ran but nothing changed." Build a new dict; return it under `updatedInput` with `permissionDecision: "allow"`.

3. **Putting decision fields at the top level instead of inside `hookSpecificOutput`.** `permissionDecision`, `updatedInput`, and `updatedToolOutput` only take effect inside `hookSpecificOutput`, and you must include the matching `hookEventName` there ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). A top-level `permissionDecision` is dropped.

4. **Using a prompt instruction where a hook is the right tool.** "Please don't touch `.env`" or "normalize the data before you use it" are requests the model can miss. The same Anthropic-way principle from the rest of this module applies: when you need a guarantee — interception or normalization that happens *every* time — use a deterministic hook, not a prompt. The model's cooperation is not a control.

## Exam focus

Hooks are the Domain 1 answer to "how do I make the agent *reliably* do/refuse X":

- **Customer Support & Code Generation** scenarios — blocking dangerous tool calls, auditing every action, sanitizing inputs before a tool runs.
- **Structured Data Extraction** — normalizing inconsistent tool/MCP outputs into one schema with a `PostToolUse` hook (pairs with the structured-output material in Domain 4).

Distractors cluster around the four pitfalls above: a matcher that "filters by path," an `updatedInput` with no `allow`, decision fields at the top level, or "instruct the model to." The correct answer is the hook configured the way the docs specify — and, between a hook and a prompt, always the hook.

## References & further reading

- [Agent SDK — Intercept and control agent behavior with hooks](https://code.claude.com/docs/en/agent-sdk/hooks) — the event list, `HookMatcher` registration, the `(input_data, tool_use_id, context)` callback signature, and the `hookSpecificOutput` fields (`permissionDecision`, `updatedInput`, `updatedToolOutput`, `additionalContext`) with the `deny` > `defer` > `ask` > `allow` precedence.
- [Claude Code — Hooks reference](https://code.claude.com/docs/en/hooks) — the full JSON input/output schema and the per-event matcher patterns that SDK callback hooks share.

## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.5: Apply Agent SDK hooks for tool call interception and data normalization.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
