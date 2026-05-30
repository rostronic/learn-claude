---
chapter: "7.5"
slug: "human-review-confidence-calibration"
title: "Human review workflows and confidence calibration"
module: "module-7-context-reliability"
sequence: 32
references:
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "Letting Claude abstain, grounding in quotes, and verifying claims with citations before answering"
  - title: "Structured outputs"
    url: "https://platform.claude.com/docs/en/build-with-claude/structured-outputs"
    type: official_docs
    covers: "Schema-compliant JSON via constrained decoding — the channel that carries per-field values and confidences"
  - title: "Increase output consistency"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency"
    type: official_docs
    covers: "Format constraints, grounding via retrieval, and asking for clarification when unsure"
---

# Human review workflows and confidence calibration

## Overview

You have an extraction or classification pipeline running on Claude. Most outputs are correct, some are wrong, and you have a limited human review budget. The design question — Task Statement 5.5 — is: **which outputs do humans look at, and how do you trust the signal that decides?**

The naive answer is "review the low-confidence ones." That's right in spirit and wrong in three specific ways the exam tests:

- **Granularity.** A document-level confidence score collapses a 30-field extraction into one number. If 29 fields are certain and one (the tax ID) is a guess, a document-level score is dragged down by the one bad field — or worse, dragged *up* by the 29 good ones so the bad field never gets seen. Review routing belongs at the **field level**: send the specific low-confidence fields to a human, not the whole document.
- **Trust.** A model's self-reported confidence is only useful if it *means* something — if outputs it tags "0.9" are right about 90% of the time. They usually aren't out of the box; models are often over-confident. You establish whether to trust the number by **calibrating against a labeled set**: bucket predictions by confidence, measure the empirical accuracy in each bucket, and report the gap.
- **Coverage.** Even with a good signal, the work you sample for ongoing QA can't be uniform random — that under-samples rare, high-risk classes. You **stratify**: sample across confidence bands and across classes so the rare-but-dangerous cases are represented.

This lesson builds all three as small, deterministic functions. None of it calls Claude — it's the *harness around* Claude's output. But it leans directly on how Claude is prompted to emit that output: abstention and grounding ([reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)), and a structured schema that carries a value *and* a confidence per field ([structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)).

## How it works

### Field-level confidence routing

The unit of review is a **field**, not a document. Model your extraction output as a mapping from field name to `{value, confidence}`, and route each field independently:

```python
def select_fields_for_review(record, threshold):
    return [name for name, field in record.items()
            if field["confidence"] < threshold]
```

This only works if Claude actually emits a per-field confidence, which is a prompting and schema decision, not an afterthought. Use **structured outputs** so the JSON is guaranteed to carry every field with its confidence and never fails to parse ([structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs): "Always valid: No more JSON.parse() errors"). And make abstention a first-class option: the [reduce-hallucinations guide](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) says to **give Claude an explicit way to say "I don't know"** rather than forcing a guess. A field where Claude abstained, or grounded its value in no supporting quote, is exactly a field that should route to review — and a low confidence is how that surfaces in the schema.

The payoff is targeting. With document-level routing you either review a whole 30-field document because of one shaky field (wasting reviewer time on 29 good ones) or you skip it because the average looked fine (missing the one bad field). Field-level routing sends a human *only* the tax ID, with the other 29 fields auto-accepted.

### Calibration against a labeled set

A confidence number is only actionable if it's **calibrated**: among predictions the model tags `p`, about a fraction `p` should actually be correct. You can't know that from the live stream — you need ground truth. So you take a **labeled** sample (predictions you've checked), bucket them by confidence, and compare the *predicted* confidence to the *empirical* accuracy in each bucket.

```python
def calibration_report(labeled):
    buckets = {}
    for row in labeled:
        b = min(int(row["confidence"] * 10), 9)   # decile; 1.0 -> bucket 9
        buckets.setdefault(b, []).append(row)
    report = []
    for b in sorted(buckets):
        rows = buckets[b]
        predicted = sum(r["confidence"] for r in rows) / len(rows)
        empirical = sum(1 for r in rows if r["correct"]) / len(rows)
        report.append({
            "bucket": b, "n": len(rows),
            "predicted": predicted, "empirical": empirical,
            "gap": abs(predicted - empirical),
        })
    return report
```

Read the output as a reliability table. If bucket 9 (`confidence ∈ [0.9, 1.0]`) shows `predicted ≈ 0.95` but `empirical = 0.70`, the model is **over-confident** there: a 0.95 tag means 70% right, so a 0.9 review threshold lets through more errors than you think. The `gap` is the size of that miscalibration. A well-calibrated model has small gaps across all buckets; a large gap tells you to move your threshold or distrust the score in that band.

This is the measurement counterpart to the consistency guidance: the [increase-consistency guide](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) prescribes grounding via retrieval and asking for clarification when unsure to *produce* a more trustworthy output — calibration is how you *verify* the confidence those techniques yield is worth trusting before you wire it to an auto-accept gate.

### Stratified sampling for QA

Once the pipeline is live you sample some fraction for ongoing human QA. Uniform random sampling is the trap: if a high-risk class is 2% of volume, a 100-item random sample expects ~2 of them, and you'll routinely draw zero — the class you most need eyes on is the one you never see. **Stratified sampling** fixes coverage: partition by a stratum key (the class, or a confidence band), allocate the sample proportionally across strata, and sample within each.

```python
import random

def stratified_sample(records, strata_key, n, rng=None):
    rng = rng or random.Random(0)
    strata = {}
    for r in records:
        strata.setdefault(r[strata_key], []).append(r)
    total = len(records)
    # Largest-remainder allocation so the counts sum to exactly n.
    raw = {k: n * len(v) / total for k, v in strata.items()}
    counts = {k: int(x) for k, x in raw.items()}
    leftover = n - sum(counts.values())
    for k in sorted(strata, key=lambda k: raw[k] - counts[k], reverse=True)[:leftover]:
        counts[k] += 1
    out = []
    for k in sorted(strata):
        out.extend(rng.sample(strata[k], counts[k]))
    return out
```

Proportional allocation keeps the QA sample's *shape* matching production while guaranteeing every stratum that has any volume contributes at least its proportional share. (If a rare class is so critical you want it *over*-represented relative to volume, you'd weight allocation by risk rather than by share — but the baseline the exam expects you to know is proportional-by-stratum, never uniform-ignoring-stratum.) The `rng` is seeded so QA runs are **reproducible**: re-running the sampler with the same seed draws the same items, which matters for auditability.

## Worked example

Put the three together on a small invoice-extraction pipeline. Claude extracts fields with per-field confidence; you route the shaky fields, calibrate the score against a labeled batch, then stratify a QA sample by document category.

```python
# 1. Field-level routing on one extracted record.
record = {
    "vendor":   {"value": "Acme Corp",   "confidence": 0.99},
    "total":    {"value": "1240.00",     "confidence": 0.97},
    "tax_id":   {"value": "12-3456789",  "confidence": 0.41},
    "due_date": {"value": "2026-06-15",  "confidence": 0.62},
}
select_fields_for_review(record, threshold=0.80)
# -> ["tax_id", "due_date"]   # the other two auto-accept

# 2. Calibrate the confidence score against a labeled batch.
labeled = [
    {"confidence": 0.95, "correct": True},
    {"confidence": 0.92, "correct": False},
    {"confidence": 0.91, "correct": True},
    {"confidence": 0.45, "correct": False},
    {"confidence": 0.41, "correct": True},
]
calibration_report(labeled)
# -> [
#   {"bucket": 4, "n": 2, "predicted": 0.43, "empirical": 0.5, "gap": 0.07},
#   {"bucket": 9, "n": 3, "predicted": 0.926..., "empirical": 0.666..., "gap": 0.259...},
# ]
# Bucket 9 is badly over-confident (gap ~0.26): a 0.9 auto-accept threshold
# is letting through about a third of its items as errors.

# 3. Stratify a QA sample of 10 across document categories.
records = [...]  # each has a "category" field, e.g. "invoice" / "receipt" / "contract"
sample = stratified_sample(records, strata_key="category", n=10)
# Proportional across categories; the rare "contract" class is represented,
# and re-running with the default seed yields the identical sample.
```

The three steps answer three different questions. Routing asks *which fields does a human touch on this document*. Calibration asks *can I trust the number that decides routing* — and bucket 9's gap says the 0.9 threshold is too loose. Stratification asks *across the whole stream, what do I pull for ongoing QA so no class hides*. The exercise implements all three to match these exact signatures and outputs.

## Anti-patterns & pitfalls

**Routing on a single document-level confidence.** Collapsing a multi-field output to one score and reviewing whole documents above/below a threshold is the headline anti-pattern. It both wastes reviewers (a human re-checks 29 correct fields to catch one) and hides errors (the average of 29 confident fields drowns out the one wrong one, so it auto-accepts). Route at the **field level**; the document score is the wrong granularity.

**Trusting raw model confidence without calibrating it.** Wiring a `confidence ≥ 0.9 → auto-accept` gate without ever checking what `0.9` empirically means is the second trap. Models are frequently over-confident; an uncalibrated 0.9 might be 70% accurate. Calibrate against a **labeled set** — bucket, measure empirical accuracy, report the gap — before you let the score gate anything. The number is an input to verify, not a truth to trust.

**Uniform random sampling for QA.** Pulling QA items uniformly at random feels fair and is wrong when classes are imbalanced: rare high-risk classes get sampled near zero, so the cases that most need review are the ones you systematically miss. **Stratify** so each class (or confidence band) is covered proportionally. "Random is unbiased" is the seductive phrasing — but unbiased coverage of a 2% class with a 100-item sample is two items, which rounds to none.

**Forcing a guess instead of allowing abstention.** Upstream of all of this: if you prompt Claude to always produce a value, a field it has no basis for comes back as a confident fabrication, and no routing threshold catches it because the confidence is high. The [reduce-hallucinations guide](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) is explicit — **give the model an out** ("say 'I don't know'") and require it to ground claims in quotes, retracting any claim it can't support. An honest low confidence (or abstention) is what makes field-level routing work at all.

## Exam focus

Task Statement 5.5 lives in Domain 5 (Context Management & Reliability) and shows up wherever a scenario has a human-in-the-loop QA budget over a high-volume Claude pipeline — extraction, classification, content moderation. The distractors are reliable:

- "Use a single confidence score per response to decide review" — wrong granularity; the answer routes per field.
- "Auto-accept everything above 0.9" — uncalibrated trust; the answer calibrates against labeled data first and reads the per-bucket gap.
- "Sample 5% at random for QA" — under-covers rare classes; the answer stratifies.

The correct option is always the one that (a) acts at field granularity, (b) verifies confidence against ground truth before trusting it, and (c) samples with coverage of the rare/high-risk strata.

## References & further reading

- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — letting Claude abstain ("I don't know"), grounding answers in direct quotes, and verifying claims with citations. The upstream half of trustworthy field confidence.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — guaranteed schema-compliant JSON via constrained decoding; the mechanism that reliably carries a `{value, confidence}` per field for field-level routing.
- [Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — format constraints, retrieval grounding, and asking for clarification when unsure; the techniques whose output confidence calibration verifies.

## Exam coverage

- **CCAF** — Domain 5 (Context Management & Reliability), Task Statement 5.5: Design human review workflows and confidence calibration.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
