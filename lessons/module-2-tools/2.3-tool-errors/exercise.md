# Structured error responses for tools — exercise

## What you're building

A **safe tool-invocation wrapper** in `tool_errors.py` that turns any tool handler into one that never throws and always returns a structured `tool_result`: successes as normal results, failures as categorized `is_error` results that tell Claude what went wrong and whether to retry.

This is CCAF Task Statement 2.2 in code: structured error responses for tools, with error categories and retryable flags, built on the catch-don't-throw rule.

No Anthropic API is involved — the tests are pure logic and need no `ANTHROPIC_API_KEY`. The four exception classes (`TransientError`, `ValidationError`, `BusinessRuleError`, `PermissionDeniedError`) are already defined for you in the starter.

## Functions to implement

```python
def classify_error(exc: Exception) -> tuple[str, bool]:
    """Return (category, retryable) for an exception.

      TransientError       -> ("transient",  True)
      ValidationError      -> ("validation", False)
      BusinessRuleError    -> ("business",   False)
      PermissionDeniedError-> ("permission", False)
      anything else        -> ("unexpected", False)   # don't blindly retry unknowns
    """

def to_tool_result(tool_use_id: str, category: str, message: str, retryable: bool) -> dict:
    """Build a STRUCTURED error tool_result:
      {
        "type": "tool_result",
        "tool_use_id": <tool_use_id>,
        "is_error": True,
        "content": {"error_category": <category>, "retryable": <retryable>, "message": <message>},
      }
    """

def safe_invoke(handler, tool_use_id: str, args: dict) -> dict:
    """Run handler(args) and ALWAYS return a tool_result — never raise.

    On success: {"type": "tool_result", "tool_use_id": <id>, "content": <handler return>}
      (no is_error, or is_error must not be True).
    On any exception: classify it, then return to_tool_result(...) with the
      exception's message (use str(exc), falling back to the category if empty).
    """
```

## Requirements

You must:

1. **Classify each known exception** into the right `(category, retryable)` pair, and classify any other exception as `("unexpected", False)`.
2. **Mark retryability correctly** — only `transient` is retryable; `validation`, `business`, `permission`, and `unexpected` are not.
3. **Build a structured error result** in `to_tool_result` with `is_error: True` and a `content` dict carrying `error_category`, `retryable`, and `message`.
4. **Return successes without an error flag** — `safe_invoke` on a handler that returns normally must produce a result that is **not** marked `is_error: True`.
5. **Pass every test in `test_tool_errors.py`.**

You must NOT:

6. **Let a handler exception propagate out of `safe_invoke`.** The wrapper must catch every exception and return a structured `is_error` result instead. An uncaught throw stops the agent loop and Claude never sees the failure — this is the central rule of the chapter, and it's graded directly (`check: anti_pattern`). Calling `safe_invoke` with a handler that raises must return a dict, never re-raise.

## How to run it

```bash
cd ~/learn-claude-work/2.3
pip install -r requirements.txt
pytest -v
```

The tests are pure logic — no API key, no network, no credits burned.

When you're ready (or stuck), run `/verify 2.3` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — the `is_error` flag and instructive error messages.
- [Give Claude custom tools](https://code.claude.com/docs/en/agent-sdk/custom-tools) — why a handler must return `is_error` instead of throwing (the loop continues vs. stops).
