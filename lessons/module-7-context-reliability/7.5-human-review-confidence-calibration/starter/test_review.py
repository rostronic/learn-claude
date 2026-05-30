"""Tests for chapter 7.5 — human review workflows and confidence calibration.

These ship complete. Run them from this directory with `pytest test_review.py -v`.
They do not touch the network and need no ANTHROPIC_API_KEY.
"""

from fixtures import LABELED, RECORD, RECORDS
from review import calibration_report, select_fields_for_review, stratified_sample


# --- field-level routing ----------------------------------------------------

def test_select_returns_only_sub_threshold_fields():
    selected = select_fields_for_review(RECORD, threshold=0.80)
    assert set(selected) == {"tax_id", "due_date"}


def test_select_excludes_confident_fields():
    selected = select_fields_for_review(RECORD, threshold=0.80)
    # The confident fields must NOT be routed to review.
    assert "vendor" not in selected
    assert "total" not in selected


def test_select_threshold_is_strict_less_than():
    # A field exactly at the threshold is NOT below it, so it is not selected.
    record = {"a": {"value": "x", "confidence": 0.80},
              "b": {"value": "y", "confidence": 0.79}}
    assert select_fields_for_review(record, threshold=0.80) == ["b"]


def test_select_returns_field_names_not_values():
    selected = select_fields_for_review(RECORD, threshold=0.80)
    # Returns the field NAMES, not the field dicts/values.
    assert all(isinstance(name, str) for name in selected)
    assert all(name in RECORD for name in selected)


# --- calibration ------------------------------------------------------------

def test_calibration_buckets_predicted_and_empirical():
    report = calibration_report(LABELED)
    by_bucket = {row["bucket"]: row for row in report}

    # Two non-empty deciles: bucket 4 ([0.4, 0.5)) and bucket 9 ([0.9, 1.0]).
    assert set(by_bucket) == {4, 9}

    # Bucket 4: confidences 0.45, 0.41 -> predicted 0.43; 1 of 2 correct -> 0.5.
    b4 = by_bucket[4]
    assert b4["n"] == 2
    assert abs(b4["predicted"] - 0.43) < 1e-9
    assert abs(b4["empirical"] - 0.5) < 1e-9
    assert abs(b4["gap"] - abs(0.43 - 0.5)) < 1e-9

    # Bucket 9: confidences 0.95, 0.92, 0.91 -> predicted ~0.9267; 2 of 3 correct.
    b9 = by_bucket[9]
    assert b9["n"] == 3
    assert abs(b9["predicted"] - (0.95 + 0.92 + 0.91) / 3) < 1e-9
    assert abs(b9["empirical"] - 2 / 3) < 1e-9


def test_calibration_reports_per_bucket_gap():
    report = calibration_report(LABELED)
    for row in report:
        assert abs(row["gap"] - abs(row["predicted"] - row["empirical"])) < 1e-9
    # The over-confident high bucket has the larger gap.
    by_bucket = {row["bucket"]: row for row in report}
    assert by_bucket[9]["gap"] > by_bucket[4]["gap"]


def test_calibration_sorted_by_bucket_and_skips_empty():
    report = calibration_report(LABELED)
    buckets = [row["bucket"] for row in report]
    assert buckets == sorted(buckets)
    # Empty deciles (e.g. bucket 0) are omitted entirely.
    assert all(row["n"] > 0 for row in report)


def test_calibration_confidence_of_one_falls_in_last_bucket():
    report = calibration_report([{"confidence": 1.0, "correct": True}])
    assert len(report) == 1
    assert report[0]["bucket"] == 9


# --- stratified sampling ----------------------------------------------------

def test_stratified_sample_returns_exactly_n():
    sample = stratified_sample(RECORDS, strata_key="category", n=10)
    assert len(sample) == 10


def test_stratified_sample_covers_more_than_one_stratum():
    sample = stratified_sample(RECORDS, strata_key="category", n=10)
    categories = {r["category"] for r in sample}
    assert len(categories) > 1
    # The rare class is represented at n=10 (10% allocation of 10/100 records).
    assert "contract" in categories


def test_stratified_sample_is_reproducible_with_default_seed():
    a = stratified_sample(RECORDS, strata_key="category", n=10)
    b = stratified_sample(RECORDS, strata_key="category", n=10)
    assert [r["id"] for r in a] == [r["id"] for r in b]


def test_stratified_sample_draws_from_the_population():
    sample = stratified_sample(RECORDS, strata_key="category", n=10)
    ids = {r["id"] for r in RECORDS}
    assert all(r["id"] in ids for r in sample)
