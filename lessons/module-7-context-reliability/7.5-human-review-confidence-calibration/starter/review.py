"""Starter skeleton for Learn Claude chapter 7.5 — human review workflows and
confidence calibration.

Implement the three functions below. See exercise.md for the full spec.
Support data lives in fixtures.py (do not edit it); tests are in test_review.py.
"""

import random
from typing import Any, Dict, List, Optional


def select_fields_for_review(record, threshold):
    """Return the field names whose confidence is BELOW the threshold.

    Args:
        record:    dict field_name -> {"value": Any, "confidence": float}.
        threshold: float — fields with confidence < threshold route to review.

    Returns:
        list[str] — the names of the fields to send to a human, i.e. every field
        whose confidence is strictly less than `threshold`. A field whose
        confidence equals the threshold is NOT selected.
    """
    # TODO: implement
    #   1. Iterate record.items() (field_name -> {"value", "confidence"}).
    #   2. Keep the field NAME when field["confidence"] < threshold (strict).
    #   3. Return the list of selected field names.
    raise NotImplementedError("Implement select_fields_for_review — see exercise.md")


def calibration_report(labeled):
    """Bucket a labeled set into deciles and report predicted vs empirical accuracy.

    Args:
        labeled: list of dicts {"confidence": float in [0, 1], "correct": bool}.

    Returns:
        list of dicts, one per NON-EMPTY decile bucket, sorted by bucket, each:
          {
            "bucket": int 0-9,        # decile: [0.0,0.1)->0 ... [0.9,1.0]->9
            "n": int,                 # rows in the bucket
            "predicted": float,       # mean confidence in the bucket
            "empirical": float,       # fraction correct in the bucket
            "gap": float,             # abs(predicted - empirical)
          }
        A confidence of exactly 1.0 falls in the last bucket (9).
    """
    # TODO: implement
    #   1. Bucket each row by decile: b = min(int(confidence * 10), 9).
    #      (The min() clamps a confidence of 1.0 into bucket 9.)
    #   2. For each NON-EMPTY bucket, in ascending bucket order, compute:
    #        n         = number of rows in the bucket
    #        predicted = mean of the rows' confidence
    #        empirical = fraction of rows where correct is True
    #        gap       = abs(predicted - empirical)
    #   3. Return a list of those dicts sorted by bucket. Skip empty buckets.
    raise NotImplementedError("Implement calibration_report — see exercise.md")


def stratified_sample(records, strata_key, n, rng=None):
    """Proportionally sample n records across the distinct values of a stratum key.

    Args:
        records:    list of dicts, each carrying record[strata_key].
        strata_key: the key whose distinct values define the strata.
        n:          total number of records to sample.
        rng:        a random.Random instance; defaults to random.Random(0) so
                    runs are reproducible.

    Returns:
        list of n sampled records. Allocation across strata is proportional to
        each stratum's share of the population, using largest-remainder rounding
        so the per-stratum counts sum to exactly n.
    """
    # TODO: implement
    #   1. If rng is None, default it to random.Random(0) (reproducible runs).
    #   2. Group records into strata by record[strata_key].
    #   3. Allocate counts proportional to each stratum's share:
    #        raw[k]    = n * len(stratum_k) / len(records)
    #        counts[k] = int(raw[k])  (floor)
    #      Then distribute the leftover (n - sum of floors) one each to the
    #      strata with the largest fractional remainders (largest-remainder
    #      rounding) so the counts sum to exactly n.
    #   4. For each stratum, rng.sample(stratum, counts[k]); concatenate and return.
    raise NotImplementedError("Implement stratified_sample — see exercise.md")
