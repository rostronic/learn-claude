# Agent SDK hooks for tool interception & normalization — exercise

## What you're building

Three Agent SDK hook callbacks, implemented as pure functions of the
`input_data` dict the SDK passes them:

- `guard_secrets` — a `PreToolUse` hook that **blocks** writes to `.env` files.
- `normalize_output` — a `PostToolUse` hook that **normalizes** a tool result to a canonical shape.
- `redirect_write` — a `PreToolUse` hook that **modifies** a Write call's input to land under `/sandbox`.

## Function signatures

```python
def guard_secrets(input_data, tool_use_id=None, context=None):
    """PreToolUse: deny when tool_name in {"Write","Edit"} AND the file_path
    basename is ".env"; else {}. Deny shape:
      {"hookSpecificOutput": {"hookEventName": ..., "permissionDecision": "deny",
                              "permissionDecisionReason": <str>}}"""

def normalize_output(input_data, tool_use_id=None, context=None):
    """PostToolUse: from input_data["tool_response"], return updatedToolOutput
    with all keys lowercased and a "units" default of "fahrenheit". Return {} if
    already canonical."""

def redirect_write(input_data, tool_use_id=None, context=None):
    """PreToolUse: for a "Write" call, return permissionDecision "allow" and
    updatedInput whose file_path is the original prefixed with "/sandbox".
    updatedInput must be a NEW dict. Return {} for non-Write tools."""
```

## Requirements

You must:

1. **In `guard_secrets`, inspect `tool_input["file_path"]`** (use `os.path.basename`) — the matcher only filters tool names, so the `.env` check lives in the callback. Deny only for `Write`/`Edit` to a `.env` file; allow (`{}`) everything else, including non-write tools targeting `.env`.
2. **Return the exact deny shape** with a non-empty `permissionDecisionReason`.
3. **In `normalize_output`, build the canonical dict** (lowercased keys, `units` defaulting to `"fahrenheit"`) and return it under `hookSpecificOutput.updatedToolOutput`. Preserve an existing `units` value.
4. **Make `normalize_output` idempotent** — return `{}` when the response is already canonical.
5. **In `redirect_write`, return `permissionDecision: "allow"` together with `updatedInput`** (a modification is ignored without the allow), and build a **new** dict.
6. **Pass every test in `test_hooks.py`.**

You must NOT:

7. **Decide from the tool name alone / ignore `tool_input`.** A hook that blocks or rewrites without reading the argument (e.g. treating the matcher as if it filtered by path) is wrong — inspect `tool_input`.
8. **Mutate `input_data["tool_input"]` in place**, or omit `permissionDecision` when returning `updatedInput`. Return a new object; include the `allow`.

Requirements 7 and 8 are graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/4.2
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — no Anthropic client, no `ANTHROPIC_API_KEY`, no API
credits. To run these for real, register each callback with
`HookMatcher(matcher=..., hooks=[callback])` under
`ClaudeAgentOptions(hooks={...})` (`pip install claude-agent-sdk`); the callback
bodies are identical.

When you're ready (or stuck), run `/verify 4.2` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Agent SDK — hooks](https://code.claude.com/docs/en/agent-sdk/hooks) — `PreToolUse`/`PostToolUse`, `permissionDecision`, `updatedInput` (needs `allow`; return a new object), and `updatedToolOutput`.
- [Claude Code — Hooks reference](https://code.claude.com/docs/en/hooks) — the full hook JSON output schema.
