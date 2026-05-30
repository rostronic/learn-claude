"""Reference implementation for Learn Claude chapter 6.2 — batch processing strategy.

Implement the four functions below. All of it is pure logic over a (mocked)
Message Batches client — no real API calls. See exercise.md for the full spec.
"""

import time


def choose_api(workflow: dict) -> str:
    """Route a workflow to "sync" or "batch".

    The deciding factor is whether someone is BLOCKED waiting on the result.
    Blocking work (pre-merge checks, live user requests) needs synchronous
    latency; latency-tolerant work (overnight/weekly jobs) goes to batch for the
    50% cost savings.

    Args:
        workflow: dict with a boolean "blocking" key.
    Returns:
        "sync" or "batch".
    """
    # TODO: return "sync" for blocking workflows, "batch" otherwise.
    raise NotImplementedError("Implement choose_api — see exercise.md")


def build_batch_requests(documents: dict) -> list[dict]:
    """Build the requests array for a batch.

    Args:
        documents: maps your stable doc id -> document text. The doc id becomes
                   the request's custom_id, which is how results are correlated
                   back to inputs.
    Returns:
        A list of {"custom_id": <doc_id>, "params": {...Messages payload...}}.
    """
    # TODO: one request per document. Set custom_id = doc_id (this is how results
    # get correlated back later), and params to a standard Messages payload
    # (model, max_tokens >= 1, messages=[{"role": "user", "content": text}]).
    raise NotImplementedError("Implement build_batch_requests — see exercise.md")


def poll_batch(client, batch_id, sleep=time.sleep, interval=60, max_polls=1440):
    """Poll the retrieval endpoint until processing_status == "ended".

    Bounded by max_polls so a stuck batch raises instead of spinning forever.
    `sleep` is injected so tests can pass a no-op.

    Returns:
        The ended batch object.
    Raises:
        TimeoutError if the batch never ends within max_polls.
    """
    # TODO: loop up to max_polls times. Each pass: retrieve the batch via
    # client.messages.batches.retrieve(batch_id); return it when
    # processing_status == "ended"; otherwise sleep(interval) and poll again.
    # Raise TimeoutError if it never ends within max_polls (do not spin forever).
    raise NotImplementedError("Implement poll_batch — see exercise.md")


def resubmittable_ids(results) -> list[str]:
    """custom_ids worth resubmitting after a partial failure.

    Resubmit "errored" and "expired" requests (identified by custom_id). Do NOT
    resubmit "succeeded" (already done) or "canceled" (stopped on purpose).
    """
    # TODO: return the custom_ids whose result.result.type is "errored" or
    # "expired" — and nothing else.
    raise NotImplementedError("Implement resubmittable_ids — see exercise.md")
