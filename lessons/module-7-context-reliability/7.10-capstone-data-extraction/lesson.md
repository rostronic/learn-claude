---
chapter: "7.10"
slug: "capstone-data-extraction"
title: "Capstone — Structured Data Extraction"
module: "module-7-context-reliability"
sequence: 37
references:
  - title: "Structured outputs"
    url: "https://platform.claude.com/docs/en/build-with-claude/structured-outputs"
    type: official_docs
    covers: "Guaranteed schema-compliant JSON via constrained decoding; strict tool use for parameter validation"
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "Allow 'I don't know', ground in direct quotes, verify-with-citations, external-knowledge restriction"
  - title: "Citations"
    url: "https://platform.claude.com/docs/en/build-with-claude/citations"
    type: official_docs
    covers: "Claim → source mapping with cited_text, document_index, and a location; guaranteed valid pointers"
  - title: "Increase output consistency"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency"
    type: official_docs
    covers: "Specify output format, constrain with examples, retrieval grounding, ask for clarification when unsure"
---

# Capstone — Structured Data Extraction

## Overview

A document-extraction pipeline takes an unstructured document — an invoice, a contract, a lab report, a loan application — and returns a populated record: vendor name, total amount, due date, line items. It is one of the most common production uses of Claude, and one of the easiest to build *badly*. The failure mode is almost always the same: someone prompts "extract the invoice fields as JSON," parses the model's prose with a regex or `json.loads`, and ships it. It works in the demo and then, in production, the model wraps the JSON in a markdown fence, invents a `currency` field nobody asked for, hallucinates a due date the document never stated, and the downstream system that expected a clean record gets garbage with no way to tell which fields to trust.

This capstone is the architecture that makes extraction *trustworthy at scale*. It is **CCA-F Scenario 6 (Structured Data Extraction)**, and it pulls together five task statements you've met separately into one pipeline:

- **4.1** — define explicit extraction criteria so the model doesn't over-extract (false positives).
- **4.3** — validate the output against a schema and business rules, with a retry/feedback loop on failure.
- **4.4** — route low-confidence fields to human review instead of auto-accepting them.
- **5.5** — calibrate confidence and decide what needs a human.
- **5.6** — attach provenance so every extracted field maps back to the source span it came from.

The spine that holds it together is a single decision Anthropic is unambiguous about: **the model's output shape must be guaranteed by the platform, not parsed out of free text.** Structured outputs give you "Always valid: No more `JSON.parse()` errors" ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)). Everything else in the pipeline — criteria, validation, confidence, provenance — assumes you start from a parseable, schema-shaped record. This lesson is a design walkthrough, not a coding exercise: we architect the pipeline stage by stage and name the trap at each one.

## How it works

A production extraction pipeline has five stages. Each maps to a task statement and to a concrete mechanism in the official docs.

### 1. Guaranteed shape — structured outputs or strict tool use

Don't ask for JSON in prose and parse the reply. Use **structured outputs**: you supply a JSON schema via `output_config.format` with `type: "json_schema"`, and constrained decoding guarantees the response conforms — structured outputs "guarantee schema-compliant responses through constrained decoding," so they're "Always valid: No more `JSON.parse()` errors" ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)). The same page gives you the second option: **strict tool use**, which guarantees tool inputs always match your defined schemas, useful when the extraction is the input to a tool call rather than a final answer ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)).

```python
import anthropic

client = anthropic.Anthropic()

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor_name": {"type": "string"},
        "invoice_number": {"type": "string"},
        "total_amount": {"type": "number"},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "due_date": {"type": "string"},   # ISO 8601
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["description", "amount"],
            },
        },
    },
    "required": ["vendor_name", "invoice_number", "total_amount", "currency"],
}

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    output_config={"format": {"type": "json_schema", "schema": INVOICE_SCHEMA}},
    messages=[{"role": "user", "content": document_text}],
)
# response shape is guaranteed to satisfy INVOICE_SCHEMA — no defensive parsing.
```

Specifying the format precisely is also the consistency lever: the consistency guidance tells you to "specify the desired output format clearly" and constrain it, rather than hoping the model picks a stable shape ([Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)). The schema *is* that specification, enforced by decoding instead of by hope.

### 2. Explicit criteria — don't over-extract (Domain 4.1)

A schema guarantees *shape*, not *honesty*. The model can still populate `due_date` with a plausible-looking date the document never stated — a **false positive**. The fix is explicit extraction criteria in the prompt: tell the model exactly what counts as present, and what to do when a field is absent. This is the hallucination guidance applied to extraction: instruct the model that it may say it doesn't know — "give Claude permission to say 'I don't know'" — and **restrict it to the provided document** so it doesn't fill gaps from parametric memory: "instruct Claude to only use information from the provided documents" ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)).

Concretely, the schema makes optional fields nullable and the prompt sets the rule: *"If a field is not explicitly present in the document, return `null` — do not infer or estimate it."* A missing due date becomes `null`, not a guess. The same page's strongest technique applies here too: have the model **ground each field in a direct quote** before committing to it — "first extract word-for-word quotes... that are most relevant," then answer from those ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). A field with no supporting quote is a field the model shouldn't have filled. That quote becomes the provenance in stage 5.

### 3. Validation + retry/feedback loop (Domain 4.3)

Schema conformance is necessary but not sufficient. `total_amount` can be schema-valid (`"number"`) and still wrong: it might not equal the sum of `line_items`, or `due_date` might fall before the invoice date. These are **business rules**, and the schema can't express all of them. So the pipeline validates in two layers — schema (handled by structured outputs) and business rules (handled by your code) — and on failure it does **not** silently accept or silently drop. It feeds the specific failure back to the model and retries.

```python
def validate(record):
    errors = []
    line_total = sum(item["amount"] for item in record.get("line_items", []))
    if record["total_amount"] != round(line_total, 2):
        errors.append(
            f"total_amount {record['total_amount']} does not equal the sum of "
            f"line_items ({line_total}). Recheck the document or set the field you misread."
        )
    return errors

def extract_with_retry(client, document_text, max_attempts=3):
    feedback = ""
    for _ in range(max_attempts):
        record = call_with_schema(client, document_text, feedback)  # structured output
        errors = validate(record)
        if not errors:
            return record
        # feed the SPECIFIC failure back — instructive, not "try again"
        feedback = "Your previous extraction had these problems:\n- " + "\n- ".join(errors)
    raise ExtractionError(f"validation failed after {max_attempts} attempts: {errors}")
```

The feedback string matters. A retry that just says "that was wrong, try again" wastes the attempt; an instructive message — *what* was wrong and *what to check* — lets the next attempt actually converge, the same principle that governs writing good tool-error messages. Note the bounded `max_attempts`: the loop is a *correction* mechanism, not an infinite one. After the cap, you escalate (to human review, stage 4), you don't ship an invalid record.

### 4. Field-level confidence + human-review routing (Domains 4.4, 5.5)

Not every field is equally certain. A crisp printed `invoice_number` is high-confidence; a handwritten `total_amount` smudged in a scanned PDF is not. The pipeline attaches a **per-field confidence** and routes on it: fields above a threshold auto-accept, fields below it go to a **human review queue**. Critically, confidence is *per field*, not per document — a single uncertain field shouldn't dump the whole record on a human, and a confident document shouldn't auto-accept its one shaky field.

```python
REVIEW_THRESHOLD = 0.85

def route(record):
    auto, review = {}, {}
    for field, value in record["fields"].items():
        if value["confidence"] >= REVIEW_THRESHOLD:
            auto[field] = value
        else:
            review[field] = value          # human checks just this field
    return {"auto_accepted": auto, "needs_review": review}
```

This is the consistency guidance's "ask for clarification when unsure" ([Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)) made operational: low confidence doesn't become a confident guess, it becomes a question routed to a human. The threshold is a tunable business decision — a medical extraction routes more aggressively than a marketing one.

### 5. Provenance — every field maps to its source span (Domain 5.6)

The reviewer in stage 4 needs to see *where in the document* a field came from to verify it in seconds. That's the **Citations** feature: enable `citations: {"enabled": true}` on the document block, and the response carries, for each claim, a pointer back to the source with `cited_text`, `document_index`, and a location (`char_location` / `page_location`) ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)). These pointers are **guaranteed valid** — they are "guaranteed to contain valid pointers to the provided documents" ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)). So a reviewer checking `total_amount: $4,200` doesn't re-read the whole invoice; they jump to the exact span the model cited and confirm or correct it.

One compatibility note worth designing around: **Citations and Structured Outputs are not used in the same call** — Citations produces interleaved cited text blocks, structured outputs produce one schema-shaped object. The clean architecture is a **two-pass** design: a structured-outputs pass to get the schema-shaped record, and a citations-grounded pass (or a strict-tool-use call whose tool inputs carry a `source_quote` field) to attach the supporting span to each field. Either way the invariant is the same as in 7.6: a field travels with its provenance, and a field nobody can cite is a field you don't auto-accept.

## Worked example

Trace one invoice through the whole pipeline. The document is a scanned PDF, but it's OCR'd first and the resulting **plain text is fed as a plain-text document** (not a raw PDF block) — so the citations come back as `char_location` offsets into that text, not page coordinates.

1. **Shape (structured outputs).** The call uses `INVOICE_SCHEMA` above. The response is guaranteed to be an object with `vendor_name`, `invoice_number`, `total_amount`, `currency`, and the rest. No `json.loads`, no markdown-fence stripping, no `try/except` around a parse. The record comes back as: `vendor_name="Acme Corp"`, `total_amount=4200.00`, `currency="USD"`, `due_date=null` (the prompt's criteria said "return null if not present" — the scan's due date was illegible).

2. **Criteria caught a non-extraction.** Because the prompt restricted the model to the document and permitted `null`, `due_date` is honestly empty rather than a hallucinated "+30 days" guess. Each populated field also carries the word-for-word quote the model grounded it in.

3. **Validation + retry.** `validate()` runs: `line_items` sum to `$4,180`, but `total_amount` is `$4,200`. Mismatch. The pipeline feeds back *"total_amount 4200.0 does not equal the sum of line_items (4180.0); recheck the document"* and retries. On attempt 2 the model finds a line item it missed (`$20` shipping), the sum now matches `$4,200`, validation passes.

4. **Confidence routing.** Per-field confidence: `invoice_number` 0.98, `vendor_name` 0.95, `total_amount` 0.91 — all auto-accept. But `due_date` is `null` with confidence 0.40 (the model is *uncertain it's truly absent* vs. illegible), so it routes to the human review queue. The other four fields ship without a human ever touching them.

5. **Provenance.** The reviewer opening the `due_date` task sees the cited span the model *did* find near the date region — a smudged line at `char_location` 1240–1268 in the OCR'd plain text — and confirms in five seconds that it's unreadable, marking the field "absent — confirmed." The accepted fields each carry their `cited_text` too, so an auditor months later can trace `total_amount=$4,200` to the exact line on the invoice.

The output record is therefore not just `{...fields...}`; it's `{fields, provenance_per_field, auto_accepted, needs_review}` — a contract a downstream system can trust because it knows *what was verified, by whom, and against which source span*.

## Anti-patterns & pitfalls

**Parsing free text instead of using structured outputs.** Prompting "return the fields as JSON" and then `json.loads(response.text)` (often after stripping a ```` ```json ```` fence) is the single most common extraction bug, and on this exam it is **wrong**, not merely fragile. The model will eventually emit a trailing comma, a prose preamble, or an extra field, and your parser will throw in production. Structured outputs exist precisely to remove this class of error — "Always valid: No more `JSON.parse()` errors" ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)). If the extraction feeds a tool, use strict tool use for the same guarantee. Defensive parsing of free text is treating a solved problem as unsolved.

**Skipping validation because the schema "already validated it."** Schema conformance proves *shape*, not *correctness*. A `total_amount` of `99999.99` is a valid `"number"` and a wrong total. Trusting the schema to catch business-rule violations — sums that don't add up, dates out of order, totals outside a sane range — is a category error. The schema and the business-rule validator are two different layers; you need both, and the validator must drive a **retry with specific feedback**, not a silent accept.

**A retry loop that doesn't say what was wrong.** Retrying with the same prompt, or with a generic "that was incorrect, try again," wastes attempts — the model has no new information and tends to repeat the error. The retry must feed back the *specific* failure (which rule, which fields, what to check) so the next attempt can converge. And the loop must be **bounded**: after N failures you escalate to human review, you don't loop forever and you don't ship the invalid record.

**Document-level confidence instead of field-level.** Scoring "this document is 0.9 confident" and auto-accepting the whole thing buries the one field that's actually a guess. Confidence and review routing must be **per field** — the smudged total goes to a human while the crisp invoice number ships. Collapsing to a single document score either over-reviews (a human re-checks four good fields to catch one) or under-reviews (the one bad field rides along on the document's average).

**Provenance as an afterthought, or self-checking instead of source-checking.** Two related traps. First, generating the record and *then* asking the model "which part of the document supports this?" invites it to fabricate a plausible-sounding citation — the whole value of the Citations feature is that its pointers are guaranteed valid against the real document ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)), which a post-hoc free-text "where did this come from?" is not. Second, asking the *same* extraction call to also judge its own confidence and correctness conflates extraction with verification; the hallucination guidance's prescription is to **verify each claim against the source** ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)), and an independent verification pass against the document beats the extractor grading its own homework.

## Exam focus

Scenario 6 is the exam's archetypal "build a reliable extraction system" question, and it's where Domain 4 (verification/human-in-the-loop) and Domain 5 (provenance/reliability) meet. Expect the prompt to describe a high-volume document pipeline and ask you to choose the architecture.

The reliable distractors:

- **"Parse the JSON out of the model's response"** — wrong; structured outputs or strict tool use guarantee the shape.
- **"Trust the schema; no extra validation"** — wrong; schema is shape, not business correctness.
- **"Retry until it works"** (unbounded, uninstructive) — wrong; bounded + specific feedback, then escalate.
- **"One confidence score per document"** — wrong; route per field.
- **"Ask the model to cite its sources after extracting"** as free text — wrong; use Citations' guaranteed-valid pointers, and prefer an independent verification pass over self-review.

The correct answer always assembles the same spine: guaranteed shape → explicit criteria → validate + bounded instructive retry → per-field confidence routing → guaranteed provenance.

## References & further reading

- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — schema-guaranteed JSON via constrained decoding and strict tool use; the foundation of the pipeline's shape guarantee.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — allow "I don't know", restrict to provided documents, ground in direct quotes, verify each claim against its source. The basis for the explicit-criteria and verification stages.
- [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) — guaranteed-valid claim → source pointers (`cited_text`, `document_index`, location) for per-field provenance; note the incompatibility with structured outputs that motivates the two-pass design.
- [Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — specify the output format, constrain it, ground in retrieval, and ask for clarification when unsure — the confidence-routing principle.

## Exam coverage

- **CCAF** — Scenario 6: Structured Data Extraction. This capstone ties together Task Statements 4.1, 4.3, 4.4, 5.5, and 5.6.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
