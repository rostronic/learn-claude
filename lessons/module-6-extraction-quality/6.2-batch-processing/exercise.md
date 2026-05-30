# Batch processing strategies — exercise

## What you're building

A small batch-processing toolkit in `batch_strategy.py`: four pure functions that capture the judgment from the lesson — route a workload to the right API, build correlatable batch requests, poll to completion, and resubmit only the failures. No real API calls; everything runs against plain data or a mocked batch client.

## Functions to implement

```python
def choose_api(workflow: dict) -> str
    # "sync" if the workflow is blocking, else "batch".

def build_batch_requests(documents: dict) -> list[dict]
    # documents maps doc_id -> text. One request per doc; custom_id == doc_id;
    # params is a standard Messages payload.

def poll_batch(client, batch_id, sleep=time.sleep, interval=60, max_polls=1440)
    # Poll client.messages.batches.retrieve(batch_id) until processing_status
    # == "ended"; return that batch. Bounded by max_polls -> TimeoutError.

def resubmittable_ids(results) -> list[str]
    # custom_ids whose result.result.type is "errored" or "expired".
```

## Requirements

You must:

1. **Route on the blocking axis.** `choose_api` returns `"sync"` for blocking workflows and `"batch"` for latency-tolerant ones. The deciding factor is whether someone is *blocked waiting* on the result.
2. **Make the `custom_id` the doc id.** In `build_batch_requests`, each request's `custom_id` is the document's stable id, and `params` is a Messages payload (`model`, `max_tokens >= 1`, `messages`). This is what lets results correlate back to inputs.
3. **Poll until `ended`, bounded.** `poll_batch` returns the batch once `processing_status == "ended"`, sleeping `interval` between polls, and raises `TimeoutError` after `max_polls` — it must not loop forever.
4. **Resubmit only failures.** `resubmittable_ids` returns the `custom_id`s of `errored` and `expired` results only — never `succeeded` or `canceled`.
5. **Pass every test in `test_batch_strategy.py`.**

You must NOT:

6. **Route a blocking workflow to the batch API.** The batch API has no latency guarantee (up to a 24-hour window), so a blocking pre-merge check or live request must never be routed to `"batch"` to chase the 50% discount. The rubric checks this directly (`check: anti_pattern`).
7. **Resubmit succeeded or canceled requests.** Re-running finished work pays (even at half price) to redo it; `resubmittable_ids` must exclude `succeeded` and `canceled`.

## How to run it

```bash
cd ~/learn-claude-work/6.2
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests use a mocked batch client — no `ANTHROPIC_API_KEY` needed, no credits burned.

When you're ready (or stuck), run `/verify 6.2` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) — the 24-hour window, `processing_status`, polling, `custom_id` correlation, and result types.
- [Retrieve Message Batch results](https://platform.claude.com/docs/en/api/retrieving-message-batch-results) — streaming results and correlating by `custom_id`.
