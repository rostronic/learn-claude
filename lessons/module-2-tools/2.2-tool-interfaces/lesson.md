---
chapter: "2.2"
slug: "tool-interfaces"
title: "Designing tool interfaces"
module: "module-2-tools"
sequence: 6
references:
  - title: "Define tools"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use"
    type: official_docs
    covers: "Tool definition shape (name/description/input_schema); best practices for descriptions, consolidation, namespacing, response shaping; good vs. poor description example"
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "Invalid tool calls: the fix is more-detailed descriptions; instructive error messages"
---

# Designing tool interfaces

## Overview

A tool definition is a **prompt** as much as it is an API contract. When you give Claude a tool, the model reads its name, description, and input schema to decide *whether* to call it, *which* tool to pick among several, and *what arguments* to pass. Get the interface right and tool selection is reliable; get it wrong and Claude reaches for the wrong tool, omits parameters, or calls nothing at all. CCAF Task Statement 2.1 is about designing these interfaces well: clear descriptions and clear boundaries.

A client tool definition has three core parts ([Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)) — plus optional fields like `input_examples` we'll come to:

- **`name`** — a unique identifier matching `^[a-zA-Z0-9_-]{1,64}$`.
- **`description`** — "a detailed plaintext description of what the tool does, when it should be used, and how it behaves."
- **`input_schema`** — a JSON Schema object defining the expected parameters.

The exam is opinionated about which of these carries the weight, and about how to fix tool-selection problems when they appear. This lesson teaches the design rules from the docs and states those opinions plainly.

## How it works

### The description is the single most important factor

The official guidance is unambiguous: "**Provide extremely detailed descriptions. This is by far the most important factor in tool performance.**" A good description explains every detail — what the tool does, when it should be used *and when it shouldn't*, what each parameter means, and any caveats or limitations. The docs give a concrete target: "**Aim for at least 3-4 sentences per tool description, more if the tool is complex**" ([Define tools — best practices](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)).

Compare the docs' own examples. The **good** description:

```json
{
  "name": "get_stock_price",
  "description": "Retrieves the current stock price for a given ticker symbol. The ticker symbol must be a valid symbol for a publicly traded company on a major US stock exchange like NYSE or NASDAQ. The tool will return the latest trade price in USD. It should be used when the user asks about the current or most recent price of a specific stock. It will not provide any other information about the stock or company.",
  "input_schema": {
    "type": "object",
    "properties": {
      "ticker": {
        "type": "string",
        "description": "The stock ticker symbol, e.g. AAPL for Apple Inc."
      }
    },
    "required": ["ticker"]
  }
}
```

The **poor** description — `"Gets the stock price for a ticker."` with an undescribed `ticker` parameter — "is too brief and leaves Claude with many open questions about the tool's behavior and usage" ([Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)). Note what the good one carries that the poor one doesn't: what it returns (latest trade price in USD), when to use it (current/most recent price), the boundary (valid US-exchange ticker), and what it explicitly *won't* do (no other company info). Every parameter has its own description too.

### Few-shot examples are not the first fix for selection problems

When Claude picks the wrong tool or fills a parameter incorrectly, the instinct is to add few-shot examples to the prompt. **On this exam that is the wrong move.** The prescribed first fix is to improve the tool's *description*. The docs make the priority explicit — "Clear descriptions are most important, but for tools with complex inputs... you can use the `input_examples` field" — and the error-handling guidance says it directly: when a tool call is invalid, "your best bet during development is to try the request again with more-detailed `description` values in your tool definitions" ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

`input_examples` exists and is useful for *complex* inputs (nested objects, format-sensitive parameters), but it is a supplement to a strong description, not a substitute for one, and it lives *on the tool definition* — not as ad-hoc few-shot exemplars stuffed into the conversation. The boundary lives in the interface. This is not "both approaches have merit": **fix the description first.**

### Boundaries: shape the tool surface, not just each tool

Beyond the single description, the docs prescribe how the *set* of tools should be shaped ([Define tools — best practices](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)):

- **Consolidate related operations into fewer tools.** "Rather than creating a separate tool for every action (`create_pr`, `review_pr`, `merge_pr`), group them into a single tool with an `action` parameter. Fewer, more capable tools reduce selection ambiguity."
- **Use meaningful namespacing in tool names.** "When your tools span multiple services or resources, prefix names with the service (e.g., `github_list_prs`, `slack_send_message`). This makes tool selection unambiguous as your library grows."
- **Design tool responses to return only high-signal information.** "Return semantic, stable identifiers (e.g., slugs or UUIDs) rather than opaque internal references, and include only the fields Claude needs... Bloated responses waste context and make it harder for Claude to extract what matters."

These are boundary decisions: how granular each tool is, how unambiguous its name is, and how lean its output is. They determine whether Claude can navigate a growing tool library without confusion.

### A linting lens

Putting the rules together, you can mechanically check a tool definition against the structural parts of this guidance — and that's exactly what the exercise builds:

```python
import re

NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

def lint_tool_definition(tool: dict) -> list[str]:
    """Return a list of issue codes for a tool definition (empty == clean)."""
    issues = []
    name = tool.get("name", "")
    if not NAME_RE.match(name):
        issues.append("name_invalid")

    desc = tool.get("description", "") or ""
    if not desc.strip():
        issues.append("description_missing")
    elif _sentence_count(desc) < 3:           # docs: aim for at least 3-4 sentences
        issues.append("description_too_thin")

    schema = tool.get("input_schema", {})
    props = schema.get("properties", {})
    for pname, pschema in props.items():
        if not (pschema.get("description") or "").strip():
            issues.append(f"param_missing_description:{pname}")
    for req in schema.get("required", []):
        if req not in props:                  # required names must be real properties
            issues.append(f"required_not_in_properties:{req}")
    return issues

def _sentence_count(text: str) -> int:
    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])
```

The thin-description check is the load-bearing one: it enforces the single most important factor in tool performance.

## Worked example

Beyond linting a definition, the other half of designing interfaces is knowing *how to respond when tool use misbehaves* — which fix to reach for. Encoding the prescribed remedies makes the "Anthropic way" explicit:

```python
# Map a tool-use symptom to Anthropic's prescribed FIRST remedy.
FIRST_FIX = {
    "wrong_tool_selected":            "improve_description",   # not few-shot examples
    "missing_required_parameter":     "improve_description",   # more-detailed descriptions
    "too_many_overlapping_tools":     "consolidate_tools",     # action param, fewer tools
    "ambiguous_names_across_services": "add_namespacing",      # github_*, slack_*
    "responses_bloat_context":        "shape_responses",       # high-signal fields only
}

def first_fix_for(symptom: str) -> str:
    try:
        return FIRST_FIX[symptom]
    except KeyError:
        raise ValueError(f"no prescribed fix for symptom {symptom!r}")

# The exam's headline opinion, made executable:
assert first_fix_for("wrong_tool_selected") == "improve_description"
assert first_fix_for("wrong_tool_selected") != "add_few_shot_examples"
```

Walking the mapping:

- **Wrong tool selected / missing parameter → improve the description.** This is the first fix the docs name; few-shot examples in the prompt are not the lever. Spell out what the tool does, when to use it, and what each parameter means.
- **Too many overlapping tools → consolidate.** Three near-identical PR tools become one `manage_pr` with an `action` parameter, cutting selection ambiguity.
- **Ambiguous names across services → namespace them.** `list` and `send` become `github_list_prs` and `slack_send_message`.
- **Responses bloat the context → shape them.** Return stable identifiers and only the fields Claude needs for its next step.

Each remedy comes straight from the Define tools best-practices list — the design rules of the interface, not prompt patches layered on top.

## Anti-patterns & pitfalls

CCAF Task Statement 2.1 tempts you with fixes that live outside the tool interface. They fail because the interface is where the information belongs:

1. **Thin, vague descriptions.** `"Gets the stock price for a ticker."` is the docs' own example of a *poor* description — too brief, leaving Claude guessing about behavior, boundaries, and return value. It's the number-one cause of unreliable tool use. Write at least 3–4 sentences covering what, when, when-not, parameters, and limits.
2. **Reaching for few-shot examples to fix tool selection.** This is the headline trap on this exam. When Claude picks the wrong tool, the prescribed first fix is a *better description*, not exemplars bolted into the prompt. (`input_examples` on the definition helps for genuinely complex inputs — but only after the description is strong, and as part of the interface.)
3. **A separate tool for every micro-action.** `create_pr`, `review_pr`, `merge_pr` as three tools multiplies selection ambiguity. Consolidate into one tool with an `action` parameter — fewer, more capable tools are easier to choose among.
4. **Colliding, un-namespaced names.** `list`, `send`, `get` across multiple services give Claude no way to disambiguate as the library grows. Prefix with the service: `github_list_prs`, `slack_send_message`.
5. **Undocumented parameters and bloated responses.** A property with no `description`, or a tool that returns opaque internal references and every field of a record, wastes the model's effort and context.

The prescribed approach: **put the information in the interface — extremely detailed descriptions first, clear parameter docs, consolidated and namespaced tools, and lean high-signal responses. When tool use misbehaves, fix the description before you touch the prompt.**

## Exam focus

This is foundational to every tool-using scenario, and the sample questions hit it directly:

- **Scenario 1 (Customer Support Resolution Agent)** and **Scenario 6 (Structured Data Extraction)** — agents whose reliability hinges on calling the right tool with the right arguments.
- The official sample question for Domain 2 (`ccaf-d2-2.1-001`) asks what to do when Claude selects the wrong tool; the keyed answer is **improve the tool description**, with "add few-shot examples" as the headline distractor. Expect that exact framing.

The reliable tell: the correct answer keeps the fix *inside the tool definition* (description, schema, consolidation, naming). Distractors move the fix *outside* it (few-shot examples in the prompt, more tools, prompt engineering around a weak description).

## References & further reading

- [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — the definition shape (`name`/`description`/`input_schema`), the best-practices list (detailed descriptions, consolidation, namespacing, response shaping), and the good-vs-poor description examples. The single best reference for this lesson.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — confirms that the fix for invalid/missing-parameter tool calls is more-detailed `description` values, and that error messages should be instructive.

## Exam coverage

- **CCAF** — Domain 2 (Tool Design & MCP Integration), Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
