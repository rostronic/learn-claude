# Structured output with tool use & JSON schemas — exercise

## What you're building

Implement three helpers in `structured_output.py` that enforce structured output via `tool_use` instead of free-text JSON: build an extraction tool, force its selection, and read the structured result (raising rather than scraping text).

The tests mock the Anthropic response, so no API key is needed.

## Function signatures

```python
def extraction_tool(name, properties, required):
    """Return a Claude tool dict: {name, description, input_schema} where input_schema
    is a JSON-schema object with the given properties and required list."""

def force_tool_choice(name):
    """Return the tool_choice value that forces the named tool: {"type": "tool", "name": name}."""

def parse_tool_result(response, tool_name):
    """Return the input dict from the matching tool_use block in response.content.
    Raise ValueError if no such tool_use block exists (the model returned text)."""
```

## Requirements

You must:

1. **`extraction_tool`** returns `{"name", "description", "input_schema"}` where `input_schema` is `{"type": "object", "properties": <properties>, "required": <required>}`.
2. **`force_tool_choice`** returns `{"type": "tool", "name": name}` (forced specific tool).
3. **`parse_tool_result`** returns the `.input` of the `tool_use` block whose `.name == tool_name`.
4. **`parse_tool_result` raises `ValueError`** if the response has no matching `tool_use` block (e.g. the model returned only text) — do not fall back to parsing JSON out of text.
5. **Pass every test in `test_structured_output.py`.**

You must NOT:

6. **Parse JSON out of the model's free-text output** anywhere. Structured output comes from the `tool_use` block's `input`; if it isn't there, raise. (And in real calls you'd force the tool with `force_tool_choice` / `tool_choice: "any"` rather than `"auto"`.)

Requirement 6 is graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/1.3
pip install -r requirements.txt
pytest -v
```

No `ANTHROPIC_API_KEY` needed — the tests mock the response.

When you're ready (or stuck), run `/verify 1.3` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first.
- [Tool use with Claude](https://platform.claude.com/docs/en/build-with-claude/tool-use) — `input_schema` and `tool_choice` modes.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — reading the `tool_use` block.
