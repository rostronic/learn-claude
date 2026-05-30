# Validation, retry & feedback loops for extraction — exercise

## What you're building

Implement `extract_with_retry` in `extraction_loop.py`. It's the quality loop from the lesson: force a structured extraction, validate the *values*, and when validation fails, retry with the **specific** errors fed back so the model self-corrects — bounded by a hard attempt cap.

## Function signature

```python
def extract_with_retry(client, document, tool, validate, max_attempts=3):
    """
    Args:
        client:       an anthropic.Anthropic() instance.
        document:     str — the source text to extract from.
        tool:         dict — the Claude tool-use schema to force (use INVOICE_TOOL).
        validate:     callable(data: dict) -> list[str] — validation error strings;
                      an empty list means the extraction is valid.
        max_attempts: int — hard cap on attempts (a backstop, not the stop signal).

    Returns:
        The validated extraction dict (first one where validate() returns []).

    Raises:
        ExtractionFailed: if validate() still reports errors after max_attempts.
    """
```

`INVOICE_TOOL` and `validate_invoice` are provided in `invoice.py`. `ExtractionFailed` is already defined in `extraction_loop.py`.

## Requirements

You must:

1. **Force the tool every attempt.** Pass `tool_choice={"type": "tool", "name": tool["name"]}` on every `client.messages.create` call — including retries — so a correction can never escape as free text. Read the extraction off the `tool_use` block's `input`.
2. **Validate the values and return on success.** Call `validate(data)`; if it returns an empty list, return `data` immediately. That empty-list result is the loop's only success exit.
3. **Retry WITH the specific errors.** When `validate` returns errors, append the assistant turn, then a `user` message whose `tool_result` block reports the exact error strings (set `is_error: True`), and loop again. The model must see *what was wrong*, not just "try again."
4. **Bound the loop and surface failure.** Cap attempts at `max_attempts`. If the validator still reports errors after the last attempt, `raise ExtractionFailed(errors, max_attempts)` carrying the unresolved errors.
5. **Pass every test in `test_extraction_loop.py`.**

You must NOT:

6. **Retry without feeding the specific validation errors back** (a blind "try again" / resample). The error feedback *is* the mechanism — a retry that omits it is just paying twice for the same coin flip. The rubric checks for this directly.
7. **Treat a schema-valid extraction as correct and skip the semantic check.** The forced `tool_use` guarantees shape, not that the numbers add up. You must run `validate` and react to its result; don't return the first extraction unconditionally.

These two anti-patterns are graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/6.1
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests mock the Anthropic client — no `ANTHROPIC_API_KEY` needed, no credits burned. After the tests pass you can set `ANTHROPIC_API_KEY` and run `python extraction_loop.py` to try the loop against the real API on `SAMPLE_INVOICE`.

When you're ready (or stuck), run `/verify 6.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — the `tool_use` `input` and the `tool_result` block (with `is_error`) you use for feedback.
- [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — forcing a specific tool with `tool_choice`.
