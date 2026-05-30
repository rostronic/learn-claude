# Human review workflows and confidence calibration — exercise

## What you're building

Implement the three functions in `review.py` that make up a human-review harness over a Claude extraction pipeline: route low-confidence **fields** to review, **calibrate** the confidence score against a labeled set, and **stratify** a QA sample so rare classes are covered. Support data is in `fixtures.py` (don't edit it); the test suite is `test_review.py`.

## Function signatures

```python
def select_fields_for_review(record, threshold):
    """record: dict field_name -> {"value", "confidence": float}.
    Return the list of field names whose confidence is STRICTLY below threshold."""

def calibration_report(labeled):
    """labeled: list of {"confidence": float in [0,1], "correct": bool}.
    Bucket into deciles [0.0,0.1)->0 ... [0.9,1.0]->9 (1.0 falls in bucket 9).
    For each NON-EMPTY bucket return {bucket, n, predicted, empirical, gap},
    where predicted = mean confidence, empirical = fraction correct,
    gap = abs(predicted - empirical). Return a list sorted by bucket."""

def stratified_sample(records, strata_key, n, rng=None):
    """Proportionally sample n records across the distinct values of
    record[strata_key]. Default rng = random.Random(0) (deterministic).
    Allocate counts proportional to each stratum's share using
    largest-remainder rounding so counts sum to exactly n, then sample
    within each stratum."""
```

## Requirements

You must:

1. **Route at the field level.** `select_fields_for_review` returns the field *names* whose `confidence` is **strictly less than** `threshold` — a field exactly at the threshold is not selected. Do not collapse the record to one document-level score.
2. **Bucket correctly.** `calibration_report` buckets by decile with `min(int(confidence * 10), 9)` so a confidence of exactly `1.0` lands in bucket 9. Skip empty buckets; return the list sorted ascending by `bucket`.
3. **Report the per-bucket gap.** Each bucket dict includes `predicted` (mean confidence), `empirical` (fraction correct), and `gap = abs(predicted - empirical)`.
4. **Stratify proportionally and deterministically.** `stratified_sample` allocates per-stratum counts proportional to each stratum's share, uses largest-remainder rounding so the counts sum to exactly `n`, defaults `rng` to `random.Random(0)`, and samples within each stratum. Two calls with the default seed must return the identical sample.
5. **Pass every test in `test_review.py`.**

You must NOT:

6. **Route on a single document-level confidence score.** Don't reduce the record to one number (an average, a min, a max) and decide review for the whole document. The unit of review is the field; an uncalibrated document average both wastes reviewers and hides errors.
7. **Sample uniformly / at random ignoring strata.** No `rng.sample(records, n)` over the flat population. That under-covers rare classes — the whole point of stratifying is that the rare, high-risk class is represented.

Requirements 6 and 7 are graded directly by the rubric (`check: anti_pattern`). The verifier reads your code for them; they fail the rubric whether or not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/7.5
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure deterministic logic — no network, no `ANTHROPIC_API_KEY`, no API credits.

When you're ready (or stuck), run `/verify 7.5` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — the schema mechanism that reliably carries a `{value, confidence}` per field, which is what field-level routing consumes.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — why an honest low confidence (and abstention) upstream is what makes routing work.
