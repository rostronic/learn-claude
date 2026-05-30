# Capstone — Structured Data Extraction — exercise

## What you're building

This is a **design exercise**, not a coding one. You'll architect a document-extraction pipeline for a real scenario and write it up as `design.md`. There's no `starter/` and no `pytest` — the verifier grades your written architecture against the rubric.

Write your design to `~/learn-claude-work/7.10/design.md`. Create the directory if it doesn't exist:

```bash
mkdir -p ~/learn-claude-work/7.10
$EDITOR ~/learn-claude-work/7.10/design.md
```

## The scenario

A lending company processes ~5,000 incoming **loan-application documents** per day (scanned PDFs and uploaded forms). Each document should yield a structured record: `applicant_name`, `annual_income`, `loan_amount`, `loan_purpose`, `employment_status`, and a list of `declared_debts` (each with a `creditor` and `balance`). Records feed an automated underwriting system. Wrong or hallucinated fields cause real financial decisions, so the pipeline must be auditable and must not silently emit fields it isn't sure about.

Design the extraction pipeline.

## What your `design.md` must cover

Address each of the five stages explicitly. For each, state your decision **and** why the alternatives are wrong.

1. **Extraction schema via structured outputs.** Define the JSON schema for the record (field names, types, which are required vs. nullable). State that you'll use **structured outputs** (`output_config.format`, `type: "json_schema"`) — or strict tool use — to guarantee the shape, and explain why you are *not* parsing free-text JSON out of the model's reply.

2. **Explicit criteria to reduce false positives.** Describe the prompt-level criteria that stop the model from inventing fields: the "return `null` if not explicitly present" rule, restricting the model to the provided document (no outside knowledge), and grounding each field in a direct quote. Pick at least one field where over-extraction is a real risk for *this* scenario and say how your criteria prevent it.

3. **Validation + retry/feedback loop.** List at least two **business rules** the schema cannot express (e.g. `loan_amount` within a policy band, `declared_debts` balances summing sanely against income). Describe the loop: validate, and on failure feed the *specific* error back to the model and retry, bounded by a max attempt count, then escalate. State explicitly that you do **not** silently accept or silently drop on validation failure.

4. **Field-level confidence + human-review routing.** Describe how each field carries its own confidence, how a threshold routes individual low-confidence fields to a human review queue while high-confidence fields auto-accept, and why this is **per field**, not per document. Name the field most likely to need review in this scenario.

5. **Per-field provenance.** Describe how each field maps back to the source span it came from using the **Citations** feature (`cited_text`, `document_index`, location), why those pointers are guaranteed valid, and how a reviewer uses them. Address the structured-outputs / Citations incompatibility (e.g. a two-pass design).

A short architecture diagram or staged list (input → shape → criteria → validate/retry → confidence-route → provenance → output record) is encouraged.

## What you must NOT do

- Do **not** propose parsing the model's free-text output (regex, `json.loads` on prose, stripping markdown fences) instead of structured outputs / strict tool use.
- Do **not** skip the validation + retry loop, or rely on the schema alone to guarantee correctness.

These are graded directly (`check: anti_pattern`). A design that parses free text or has no validation/retry loop fails the rubric regardless of how polished the rest is.

When you're ready (or stuck), run `/verify 7.10` and I'll grade your design.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — the shape guarantee.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — null-on-absent, document restriction, quote grounding, verify against source.
- [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) — guaranteed-valid per-field provenance pointers.
- [Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — specify/constrain the output format; ask for clarification when unsure.
