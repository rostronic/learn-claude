"""Tests for the batch strategy toolkit. Pure logic + a mocked batch client."""

from types import SimpleNamespace

import pytest

from batch_strategy import (
    build_batch_requests,
    choose_api,
    poll_batch,
    resubmittable_ids,
)


def _result(custom_id, type_):
    """A fake batch result row: result.custom_id and result.result.type."""
    return SimpleNamespace(custom_id=custom_id, result=SimpleNamespace(type=type_))


class _Batches:
    def __init__(self, statuses):
        # processing_status to return on each successive retrieve() call.
        self._statuses = list(statuses)
        self.retrieve_calls = 0

    def retrieve(self, batch_id):
        status = self._statuses[min(self.retrieve_calls, len(self._statuses) - 1)]
        self.retrieve_calls += 1
        return SimpleNamespace(id=batch_id, processing_status=status)


class _MockClient:
    def __init__(self, statuses):
        self.messages = SimpleNamespace(batches=_Batches(statuses))


# --- choose_api ------------------------------------------------------------

def test_blocking_workflow_routes_to_sync():
    """A blocking pre-merge check must NOT go to batch (no latency guarantee)."""
    assert choose_api({"name": "pre-merge check", "blocking": True}) == "sync"


def test_latency_tolerant_workflow_routes_to_batch():
    """An overnight report is latency-tolerant — batch it for the 50% savings."""
    assert choose_api({"name": "overnight tech-debt report", "blocking": False}) == "batch"


# --- build_batch_requests --------------------------------------------------

def test_custom_id_is_the_doc_id_for_correlation():
    docs = {"doc-001": "alpha", "doc-002": "beta"}
    requests = build_batch_requests(docs)

    assert {r["custom_id"] for r in requests} == {"doc-001", "doc-002"}
    by_id = {r["custom_id"]: r for r in requests}
    assert by_id["doc-001"]["params"]["messages"][0]["content"] == "alpha"
    assert by_id["doc-001"]["params"]["max_tokens"] >= 1  # batched requests need max_tokens >= 1


# --- poll_batch ------------------------------------------------------------

def test_poll_returns_once_status_is_ended():
    client = _MockClient(["in_progress", "in_progress", "ended"])
    calls = []
    batch = poll_batch(client, "msgbatch_1", sleep=calls.append, interval=5)

    assert batch.processing_status == "ended"
    assert client.messages.batches.retrieve_calls == 3
    assert calls == [5, 5]  # slept between the two in_progress polls, not after ended


def test_poll_is_bounded_and_raises_if_never_ends():
    client = _MockClient(["in_progress"])  # never ends
    with pytest.raises(TimeoutError):
        poll_batch(client, "msgbatch_stuck", sleep=lambda _: None, max_polls=3)
    assert client.messages.batches.retrieve_calls == 3  # did not spin forever


# --- resubmittable_ids -----------------------------------------------------

def test_only_errored_and_expired_are_resubmitted():
    results = [
        _result("doc-001", "succeeded"),
        _result("doc-002", "errored"),
        _result("doc-003", "expired"),
        _result("doc-004", "canceled"),
        _result("doc-005", "succeeded"),
    ]
    assert resubmittable_ids(results) == ["doc-002", "doc-003"]


def test_all_succeeded_means_nothing_to_resubmit():
    results = [_result("a", "succeeded"), _result("b", "succeeded")]
    assert resubmittable_ids(results) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
