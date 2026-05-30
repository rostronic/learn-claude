"""Tests for run_pipeline — error propagation across a multi-stage pipeline.

These tests pin the propagation contract: failures must be surfaced (never
swallowed), attributed (provenance = the failing stage name), transient
failures retried, and a failure must NOT crash the run or thread a missing
value downstream.
"""

import pytest

from fixtures import ok_stage, transient_then_ok, hard_fail_stage
from pipeline import run_pipeline


def test_all_ok_pipeline_runs_in_order():
    stages = [
        ("alpha", ok_stage("alpha")),
        ("beta", ok_stage("beta")),
        ("gamma", ok_stage("gamma")),
    ]
    report = run_pipeline(stages, [], max_retries=1)

    assert report["status"] == "ok"
    assert report["errors"] == []
    # Results are recorded in execution order, one per stage.
    stage_order = [r["stage"] for r in report["results"]]
    assert stage_order == ["alpha", "beta", "gamma"]
    # The value threaded forward, accumulating each stage's name.
    assert report["results"][-1]["value"] == ["alpha", "beta", "gamma"]


def test_transient_failure_is_retried_then_succeeds():
    stages = [
        ("alpha", ok_stage("alpha")),
        ("beta", transient_then_ok("beta", fail_times=1)),
        ("gamma", ok_stage("gamma")),
    ]
    report = run_pipeline(stages, [], max_retries=1)

    assert report["status"] == "ok"
    assert report["errors"] == []
    stage_order = [r["stage"] for r in report["results"]]
    assert stage_order == ["alpha", "beta", "gamma"]


def test_transient_failure_exhausts_retries_and_fails():
    # Fails twice, but only one retry is allowed -> ends as a failure.
    stages = [
        ("alpha", ok_stage("alpha")),
        ("beta", transient_then_ok("beta", fail_times=2)),
        ("gamma", ok_stage("gamma")),
    ]
    report = run_pipeline(stages, [], max_retries=1)

    assert report["status"] == "failed"
    assert [e["stage"] for e in report["errors"]] == ["beta"]
    # A retryable failure is reported as recoverable.
    assert report["errors"][0]["recoverable"] is True


def test_hard_failure_stops_pipeline_with_provenance():
    stages = [
        ("alpha", ok_stage("alpha")),
        ("beta", hard_fail_stage("beta")),
        ("gamma", ok_stage("gamma")),
    ]
    report = run_pipeline(stages, [], max_retries=1)

    assert report["status"] == "failed"
    # Provenance: the errors list names the stage that actually failed.
    assert [e["stage"] for e in report["errors"]] == ["beta"]
    # Downstream stage gamma must NOT have executed.
    assert "gamma" not in [r["stage"] for r in report["results"]]
    # alpha ran and was recorded before the failure.
    assert [r["stage"] for r in report["results"]] == ["alpha"]


def test_failure_is_not_swallowed():
    stages = [("alpha", hard_fail_stage("alpha", error="boom"))]
    report = run_pipeline(stages, [], max_retries=1)

    # The error is surfaced, not swallowed: errors list is non-empty and carries
    # the instructive message and provenance.
    assert report["status"] == "failed"
    assert len(report["errors"]) >= 1
    assert report["errors"][0]["stage"] == "alpha"
    assert report["errors"][0]["error"] == "boom"


def test_hard_failure_is_not_recoverable():
    stages = [("alpha", hard_fail_stage("alpha"))]
    report = run_pipeline(stages, [], max_retries=3)

    assert report["status"] == "failed"
    assert report["errors"][0]["recoverable"] is False


def test_run_pipeline_never_raises():
    # Even with a hard failure mid-pipeline, run_pipeline returns a structured
    # aggregate rather than raising — one stage's failure is contained.
    stages = [
        ("alpha", ok_stage("alpha")),
        ("beta", hard_fail_stage("beta")),
    ]
    try:
        report = run_pipeline(stages, [], max_retries=1)
    except Exception as exc:  # pragma: no cover
        pytest.fail("run_pipeline must not raise; it raised %r" % exc)

    assert report["status"] == "failed"


def test_empty_pipeline_is_ok():
    report = run_pipeline([], "seed", max_retries=1)
    assert report["status"] == "ok"
    assert report["results"] == []
    assert report["errors"] == []
