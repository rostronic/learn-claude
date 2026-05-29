---
chapter: "1.3"
slug: "structured-output"
title: "Structured output with tool use & JSON schemas"
module: "module-1-prompting"
sequence: 4
references:
  - title: "Define tools (tool_use, input_schema, tool_choice)"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use"
    type: official_docs
    covers: "Defining tools with input_schema (JSON Schema); tool_choice modes auto/any/tool; strict:true"
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "stop_reason tool_use; tool_use block shape (id/name/input); reading the structured input"
---

# Structured output with tool use & JSON schemas

## Overview

When you need Claude to return data your code can consume — an extracted invoice, a classification, a list of findings — the unreliable way is to ask for JSON in the prompt and parse it out of the text. Models occasionally emit a stray comma, a markdown fence, or a chatty preamble, and your parser breaks. The reliable way is **tool use with a JSON schema**: you define a tool whose `input_schema` *is* your output shape, and Claude fills it in. The exam calls this "the most reliable approach for guaranteed schema-compliant structured output, eliminating JSON syntax errors" (CCAF 4.3).

This builds on what you saw in the agentic-core module: a `tool_use` response is structured by construction. Here we're not executing a tool — we're using the tool *call itself* as the typed output channel.

## How it works

You pass a tool whose `input_schema` is a JSON Schema describing the fields you want. When Claude "calls" it, the call's `input` is your data, already parsed and schema-shaped — you read it off the `tool_use` block ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). The key control is **`tool_choice`**, and the exam tests the three modes precisely:

- **`"auto"`** — the model may call a tool *or* return plain text. Wrong for guaranteed extraction: it can answer in prose and skip the tool.
- **`"any"`** — the model *must* call a tool but picks which. Use when several extraction schemas exist and the document type is unknown.
- **`{"type": "tool", "name": "extract_metadata"}`** — forces a *specific* tool. Use when exactly one extraction must run (e.g. before enrichment steps).

For structured output you almost always want `"any"` or a forced tool — never `"auto"`, because `"auto"` is exactly the door through which free-text answers escape your schema.

```python
import anthropic

INVOICE = {
    "name": "record_invoice",
    "description": "Record the structured fields extracted from an invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string"},
            "total": {"type": "number"},
            "due_date": {"type": ["string", "null"]},   # nullable: may be absent
            "status": {"type": "string", "enum": ["paid", "unpaid", "unclear"]},
        },
        "required": ["vendor", "total", "status"],       # due_date intentionally optional
    },
}

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[INVOICE],
    tool_choice={"type": "tool", "name": "record_invoice"},  # force it — no text escape
    messages=[{"role": "user", "content": invoice_text}],
)
data = next(b.input for b in resp.content if b.type == "tool_use")  # already a dict
```

Two schema-design rules the exam stresses:

1. **Make fields optional/nullable when the source might not contain them.** A `required` field the document lacks pressures the model to *fabricate* a value. Marking `due_date` nullable lets it return nothing honestly (CCAF 4.3).
2. **Give ambiguity an escape hatch.** Add enum values like `"unclear"` for uncertain cases, and an `"other"` + free-text `detail` field for extensible categories, so the model isn't forced to mis-bucket.

One thing schemas **don't** fix: semantic errors. "Strict JSON schemas via tool use eliminate syntax errors but do not prevent semantic errors" — line items that don't sum to the total, a value placed in the wrong field. The schema guarantees *shape*, not *correctness*; that's what validation/retry loops (a later chapter) are for. You can also add `strict: true` to a tool definition to guarantee the inputs match your schema exactly ([Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)).

## Worked example

A small structured-output toolkit: build an extraction tool, force it, and read the result — refusing to fall back to text parsing.

```python
def extraction_tool(name, properties, required):
    return {
        "name": name,
        "description": f"Extract structured fields: {', '.join(properties)}.",
        "input_schema": {"type": "object", "properties": properties, "required": required},
    }

def force_tool_choice(name):
    return {"type": "tool", "name": name}

def parse_tool_result(response, tool_name):
    """Return the structured input from the matching tool_use block.
    Raises if the model returned text instead of calling the tool."""
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input          # already a dict — no JSON parsing
    raise ValueError(f"model did not call {tool_name!r}; refusing to parse free text")
```

`parse_tool_result` deliberately *raises* rather than scraping JSON out of `response`'s text. If you forced the tool with `force_tool_choice`, this branch shouldn't happen — and if it does, that's a signal to fix the request, not to start regexing prose.

## Anti-patterns & pitfalls

1. **Parsing JSON out of free text.** Asking "respond with JSON" and running `json.loads` on the message body. This is the brittle path the whole task statement exists to replace — markdown fences, preambles, and trailing commas all break it. Use `tool_use`.
2. **`tool_choice: "auto"` for guaranteed extraction.** With `"auto"` the model can answer in prose and never call your tool. Use `"any"` (unknown schema) or a forced `{"type": "tool", "name": …}` (specific extraction).
3. **All fields `required`.** Forcing fields the source may lack makes the model fabricate values. Mark genuinely-optional fields nullable/optional.
4. **No escape hatch for ambiguity.** Rigid enums with no `"unclear"`/`"other"` force the model to mis-classify edge cases. Add them.
5. **Trusting shape as correctness.** A schema-valid result can still be semantically wrong (totals that don't add up). Validate the values; don't assume the schema did.

## Exam focus

This is the backbone of **CCAF Scenario 6 (Structured Data Extraction)**: extraction tools with JSON schemas, `tool_choice` to guarantee a call, nullable fields to prevent fabrication, and enums with `"other"`/`"unclear"` for messy real-world documents. The reliable distractor is "prompt for JSON and parse the text" or "use `tool_choice: auto`" — both let unstructured output slip through; the correct answer forces structured output through `tool_use`.

## References & further reading

- [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — `input_schema` as a JSON Schema, the `tool_choice` modes (auto/any/tool), and `strict: true`.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — reading the `tool_use` block's `input` as your structured result.

## Exam coverage

- **CCAF** — Domain 4 (Prompt Engineering & Structured Output), Task Statement 4.3: Enforce structured output using tool use and JSON schemas.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
