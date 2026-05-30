---
chapter: "6.1"
slug: "validation-retry-loops"
title: "Validation, retry & feedback loops for extraction"
module: "module-6-extraction-quality"
sequence: 24
references:
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "Reading tool_use input; the tool_result block shape and is_error for feeding failures back"
  - title: "Define tools (tool_use, input_schema, tool_choice)"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use"
    type: official_docs
    covers: "Forcing a specific extraction tool with tool_choice; input_schema as the output shape"
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "Giving the model an explicit out (e.g. 'I don't know') so it doesn't fabricate missing values"
---

# Validation, retry & feedback loops for extraction

## Overview

The previous chapter ([structured output](../../module-1-prompting/1.3-structured-output/lesson.md)) got Claude to return data that always matches your schema. But schema-valid is not the same as *correct*. A forced `tool_use` call guarantees the *shape* — the fields are present and well-typed — and nothing more. The invoice's line items can still fail to sum to its stated total; a date can land in the wrong field; a required number can be confidently fabricated. As the exam puts it, "strict JSON schemas via tool use eliminate syntax errors but do not prevent semantic errors."

This chapter closes that gap with a **validation-and-retry loop**: extract, validate the *values*, and — when validation fails — send the model a follow-up request that names exactly what was wrong so it can correct itself. This is the Domain 4 quality mechanism, and it's the difference between an extractor that's right 85% of the time and one you can put in front of a downstream system.

Two ideas do the work, and the exam tests both precisely:

- **Retry *with error feedback*.** A bare "try again" is nearly worthless. The prescribed pattern appends the *specific validation errors* to the retry so the model knows what to fix.
- **Knowing when retry is futile.** Retries fix format and structural mistakes. They cannot conjure information that simply isn't in the source document. Spending three API calls re-asking for an absent value is a bug, not a feature.

## How it works

The loop has four moving parts: an extraction tool, a validator, a feedback step, and a stop condition.

**1. Force the extraction.** As in 1.3, you define a tool whose `input_schema` is your output shape and force it with `tool_choice`, so the model can't escape into prose ([Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)). You read the structured result off the `tool_use` block's `input` ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

**2. Validate the values, not the shape.** The schema already guaranteed the shape. Your validator checks *semantics* — the things a schema can't express. The exam's worked pattern is to extract a computed value *alongside* the model's stated one and compare them: pull `calculated_total` next to `stated_total`, and flag a discrepancy; add a `conflict_detected` boolean for internally inconsistent source data. A validator returns a list of human-readable error strings; an empty list means "valid."

```python
def validate_invoice(data: dict) -> list[str]:
    """Semantic checks the JSON schema cannot enforce. Returns error strings."""
    errors = []
    items = data.get("line_items") or []
    calculated_total = round(sum(item["amount"] for item in items), 2)
    stated_total = data.get("total")
    if stated_total is not None and calculated_total != stated_total:
        errors.append(
            f"line_items sum to {calculated_total} but total is {stated_total}"
        )
    return errors
```

**3. Feed the specific errors back.** This is the crux. On a failed attempt you make a follow-up request that includes the original document, the failed extraction, and the *specific* validation errors, asking the model to correct them. Because you're already in a `tool_use` exchange, the natural shape is to append the assistant's `tool_use` turn, then a `user` turn whose `tool_result` reports the errors. The Messages API gives `tool_result` an `is_error` flag for exactly this — signaling that the tool call's output was a failure the model should react to ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)):

```python
messages.append({"role": "assistant", "content": response.content})
messages.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_block.id,
        "is_error": True,
        "content": "Validation failed:\n- " + "\n- ".join(errors)
                   + "\nReturn a corrected extraction.",
    }],
})
```

The model now sees its own prior answer *and* a precise critique of it, and re-calls the tool with a fix. Generic retries ("that wasn't right, try again") omit the critique and just resample — you're paying for another roll of the dice instead of guiding a correction.

**4. Stop on success, a cap, or futility.** The loop returns the moment validation passes. It is bounded by a small `max_attempts` cap (retries are not free, and a model that can't satisfy the validator in three tries won't in thirty). And critically: **retries only help when the fault is format or structure.** "Retries are ineffective when the required information is simply absent from the source document." If the document never stated a due date, re-asking will at best return `null` again and at worst pressure the model to invent one — the official guidance is to give the model an explicit way to say the value is missing rather than force a guess ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). A validator that flags *absence* should route to a human or mark the field unresolved, not loop.

There's one more design payoff the exam calls out. When findings are dismissed downstream (a developer waves off a flagged issue, a reviewer overrides an extraction), a `detected_pattern` field that records *which construct triggered the finding* lets you analyze false-positive patterns systematically — you learn which rules are noisy instead of guessing.

## Worked example

A complete, reusable loop. It forces the tool, validates, feeds specific errors back, caps attempts, and distinguishes a correctable failure from an absent-data failure.

```python
import anthropic

class ExtractionFailed(Exception):
    def __init__(self, errors, attempts):
        self.errors, self.attempts = errors, attempts
        super().__init__(f"unresolved after {attempts} attempt(s): {errors}")

def extract_with_retry(client, document, tool, validate, max_attempts=3):
    """Extract structured data, retrying with specific error feedback on failure.

    Returns the validated extraction dict. Raises ExtractionFailed if the
    validator still reports errors after max_attempts.
    """
    messages = [{
        "role": "user",
        "content": f"Extract the fields by calling {tool['name']}.\n\n{document}",
    }]
    errors = []
    for attempt in range(1, max_attempts + 1):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},  # force it — no prose escape
            messages=messages,
        )
        tool_block = next(b for b in response.content if b.type == "tool_use")
        data = tool_block.input

        errors = validate(data)
        if not errors:
            return data                                    # the real exit: validation passed

        # Retry WITH the specific errors appended — not a bare "try again".
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "is_error": True,
                "content": "Validation failed:\n- " + "\n- ".join(errors)
                           + f"\nCall {tool['name']} again with corrected values.",
            }],
        })

    raise ExtractionFailed(errors, max_attempts)
```

Walking through it:

- **`tool_choice` forces the named tool every attempt** — including retries — so a correction can never slip out as free text.
- **`validate` returns error strings; empty means valid.** Returning on an empty list is the only success exit; the cap is a backstop, not the signal.
- **The retry message carries the exact errors,** wrapped in a `tool_result` with `is_error: True`. The model corrects against a critique, not a vibe.
- **`ExtractionFailed` surfaces the unresolved errors.** If those errors are "field absent from source," the caller escalates to a human instead of looping — the loop refuses to manufacture data that isn't there.

To use it for invoices, you'd pass an `INVOICE_TOOL` (an `input_schema` with `vendor`, `total`, `line_items`, and a nullable `due_date`) and the `validate_invoice` from earlier. A document whose line items don't sum to the total fails on attempt 1, gets the discrepancy spelled out, and typically returns corrected on attempt 2.

## Anti-patterns & pitfalls

The exam's Task Statement 4.4 turns these directly into distractors. Each is a way of *looking* like you built a quality loop without actually building one.

1. **Blind retry — resampling without feedback.** Re-calling the model with the same prompt and hoping for a better draw. The prescribed pattern is "appending specific validation errors to the prompt on retry to guide the model toward correction." A retry that doesn't tell the model what was wrong is just paying twice for the same coin flip. **The error feedback *is* the mechanism.**
2. **Retrying when the information is absent.** Looping on a value the source never contained. "Retries are ineffective when the required information is simply absent from the source document." Re-asking can't add data; it only wastes calls and tempts fabrication. Detect absence, mark the field unresolved or escalate — don't spin.
3. **Treating schema-valid as correct.** Assuming that because the `tool_use` call matched the schema, the values are right. Tool use eliminates *syntax* errors, not *semantic* ones — totals that don't add up, a value in the wrong field. If you skip the semantic validator, you've shipped the bug the schema can't catch.
4. **Forcing the model to guess instead of giving it an out.** Marking every field `required` so the model fabricates a plausible value rather than admitting a gap. Make genuinely-optional fields nullable and let the model return "unclear"/`null`, so absence is *detectable* by your validator instead of hidden behind a confident guess ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)).
5. **An unbounded retry loop.** No cap, retrying until it passes. A model that fails the validator three times in a row is signaling something the loop can't fix (an absent value, a contradictory source, a too-strict rule). Cap attempts and surface the failure.

The throughline: **a quality loop validates the values and feeds the specific failure back, within a bound** — anything less is theater.

## Exam focus

This task statement powers **Scenario 6 (Structured Data Extraction)** and shows up in **Scenario 5 (CI)** wherever a review finding needs validating before it's posted. Reliable distractors: "just retry the request" (missing the error feedback), "the schema already guarantees correctness" (conflating syntax with semantics), and "retry until it succeeds" (no futility check, no cap). The correct answer always (a) feeds the *specific* validation errors back, (b) validates *semantics* the schema can't, and (c) stops retrying when the fault is missing source data rather than a fixable format error.

## References & further reading

- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — reading the `tool_use` `input` as your extraction, and the `tool_result` block (with `is_error`) you use to feed validation failures back for self-correction.
- [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — forcing a specific extraction tool with `tool_choice` so retries can't escape into prose, and `input_schema` as the output shape.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — giving the model an explicit "I don't know"/`null` path so absent values surface as gaps instead of fabrications, which is what tells your loop to stop retrying.

## Exam coverage

- **CCAF** — Domain 4 (Prompt Engineering & Structured Output), Task Statement 4.4: Implement validation, retry, and feedback loops for extraction quality.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
