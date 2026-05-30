---
chapter: "6.2"
slug: "batch-processing"
title: "Batch processing strategies"
module: "module-6-extraction-quality"
sequence: 25
references:
  - title: "Batch processing (Message Batches API)"
    url: "https://platform.claude.com/docs/en/build-with-claude/batch-processing"
    type: official_docs
    covers: "50% cost, 24h window/no SLA, custom_id, processing_status, polling, result types"
  - title: "Create a Message Batch (API reference)"
    url: "https://platform.claude.com/docs/en/api/creating-message-batches"
    type: official_docs
    covers: "The requests array: custom_id + params (a standard Messages create payload)"
  - title: "Retrieve Message Batch results (API reference)"
    url: "https://platform.claude.com/docs/en/api/retrieving-message-batch-results"
    type: official_docs
    covers: "Streaming results back and correlating them by custom_id; per-request result types"
---

# Batch processing strategies

## Overview

Most of what you've built so far calls the model **synchronously**: you send a request, you block, you get a response in seconds. That's the right shape when a human or a pipeline is waiting on the answer. But a large class of real work *isn't* latency-sensitive — overnight technical-debt reports, weekly compliance audits, nightly test generation, re-processing a back-catalog of documents. For those, paying full price for instant responses you don't need is waste.

The **Message Batches API** is Anthropic's answer: submit many Messages requests as one batch, let them process asynchronously, and collect the results when they're done. The trade is explicit and the exam tests it exactly: you get **50% off** standard token prices in exchange for **no latency guarantee** — "most batches finishing in less than 1 hour" but a window of up to 24 hours, after which unfinished requests expire ([Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)).

So the architectural skill here isn't "call the batch API" — it's **matching each workload to the right API**. Latency-tolerant, non-blocking work goes to batch and saves half the cost. Blocking work — anything a developer or user is actively waiting on, like a pre-merge check — stays synchronous, because "process in under 24 hours" is unacceptable when someone's blocked on the result.

## How it works

A batch is a list of independent requests, each tagged with a `custom_id` you choose. You submit the list, poll for completion, then stream the results back and **correlate each result to its request by that `custom_id`** ([Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)). Four facts drive every design decision:

- **50% cost savings.** "All usage is charged at 50% of the standard API prices." This is the entire reason to reach for batch.
- **Up to a 24-hour window, no SLA.** You can access results once all requests finish *or* after 24 hours, whichever comes first; requests that don't finish in 24 hours **expire**. There is no guaranteed completion time — planning around "usually under an hour" is not allowed for anything blocking.
- **`custom_id` correlates request to response.** Results don't necessarily come back in submission order, so the `custom_id` (unique, `^[a-zA-Z0-9_-]{1,64}$`) is how you line each result up with its input. This is also how you identify *which* requests failed for resubmission.
- **A batched request can't pause for *your* client-side tool execution and resume.** Tool use, server tools, and multi-turn conversations are all batchable ([Batch processing — what can be batched](https://platform.claude.com/docs/en/build-with-claude/batch-processing#what-can-be-batched)). The constraint is interactivity: with no open connection, if Claude requests a *client-side* tool the batched request returns with that `tool_use` and you continue it in a follow-up request — it isn't a live loop. Server-side tools (web search, code execution, MCP connectors) *do* run inside a batch via the same server-side agentic loop, returning `stop_reason: "pause_turn"` when a turn needs continuing. So a client-side agentic loop with per-turn round-trips doesn't run *inside* one batched request — batch its individual model calls, or run that loop synchronously.

Each batched request carries a standard Messages payload under `params` ([Create a Message Batch](https://platform.claude.com/docs/en/api/creating-message-batches)):

```python
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

client = anthropic.Anthropic()

batch = client.messages.batches.create(
    requests=[
        Request(
            custom_id="doc-001",                       # YOUR id — used to correlate later
            params=MessageCreateParamsNonStreaming(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Summarize document 001..."}],
            ),
        ),
        Request(custom_id="doc-002", params=...),
    ]
)
```

When the batch is created its `processing_status` is `in_progress`; it flips to `ended` once every request has finished. You **poll** the retrieval endpoint until then:

```python
import time

while True:
    batch = client.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(60)                                      # poll interval; not a busy-wait
```

Then stream results and dispatch on each request's result type ([Retrieve results](https://platform.claude.com/docs/en/api/retrieving-message-batch-results)). The four types are `succeeded`, `errored`, `expired`, and `canceled`:

```python
outcomes = {}
for result in client.messages.batches.results(batch.id):
    outcomes[result.custom_id] = result.result.type    # correlate by custom_id
```

**Handling failures means resubmitting only what failed.** `errored` and `expired` requests should be resubmitted (often with a fix — e.g. chunking a document that blew the context limit); `succeeded` requests are done; `canceled` ones you chose to stop. You identify the failures *by their `custom_id`* and build a new, smaller batch from just those — never re-running the whole set.

### Sizing batches against an SLA

When a downstream SLA exists, you size submission frequency around the 24-hour worst case. The exam's worked example: to guarantee a **30-hour** end-to-end SLA given a 24-hour batch window, submit on a **4-hour** cadence — a document arriving just after a submission waits at most ~4 hours to be included, plus up to 24 to process, comfortably under 30. The batch window is a worst case you budget around, not an average you hope for.

## Worked example

A small batch toolkit: decide the API per workload, build correlatable requests, poll to completion, and resubmit only the failures.

```python
import time


def choose_api(workflow: dict) -> str:
    """Route a workflow to the right API. The deciding factor is whether
    someone is BLOCKED waiting on the result."""
    # Blocking work (pre-merge checks, live user requests) needs synchronous
    # latency. Everything latency-tolerant (overnight/weekly jobs) goes to batch.
    return "sync" if workflow["blocking"] else "batch"


def build_batch_requests(documents: dict) -> list[dict]:
    """documents maps your stable doc id -> text. The id BECOMES the custom_id,
    which is how results get correlated back to inputs."""
    return [
        {
            "custom_id": doc_id,
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": text}],
            },
        }
        for doc_id, text in documents.items()
    ]


def poll_batch(client, batch_id, sleep=time.sleep, interval=60, max_polls=1440):
    """Poll until processing_status == 'ended'. Bounded so it can't spin forever."""
    for _ in range(max_polls):
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            return batch
        sleep(interval)
    raise TimeoutError(f"batch {batch_id} did not end within {max_polls} polls")


def resubmittable_ids(results) -> list[str]:
    """custom_ids worth resubmitting: errored + expired. NOT succeeded (done) and
    NOT canceled (you stopped them on purpose)."""
    return [r.custom_id for r in results if r.result.type in ("errored", "expired")]
```

Walking through it:

- **`choose_api` decides on one axis: blocking or not.** A pre-merge check is blocking → synchronous. An overnight report is not → batch, at half cost. Routing a blocking workflow to batch to "save money" is the headline mistake — see below.
- **`build_batch_requests` makes the `custom_id` your stable doc id,** so when results stream back out of order you can still attribute each one. Lose that mapping and a 50,000-document batch becomes an unattributable pile.
- **`poll_batch` waits for `ended` and is bounded** by `max_polls` so a stuck batch raises instead of looping forever. The injected `sleep` keeps it testable.
- **`resubmittable_ids` retries only `errored`/`expired`,** identified by `custom_id`. Re-running `succeeded` requests would pay (even at half price) to redo finished work.

## Anti-patterns & pitfalls

Task Statement 4.5 turns each of these into a distractor:

1. **Sending blocking work to the batch API for the discount.** The 50% saving tempts you to batch *everything*. But a pre-merge check that gates a developer's merge cannot tolerate "done within 24 hours, no promises." Blocking workflows stay synchronous; only latency-tolerant work batches. This is the single most-tested judgment in this task statement.
2. **Planning around "usually under an hour."** Treating the typical sub-hour completion as a latency guarantee. There is **no SLA**; the contract is the 24-hour window with expiry. Any design that *requires* fast completion is mis-using the API.
3. **Resubmitting the whole batch on partial failure.** If 200 of 50,000 requests `errored`, you resubmit those 200 (by `custom_id`), not all 50,000. Re-running succeeded work wastes money and time.
4. **Losing the `custom_id` correlation.** Assuming results return in submission order, or not setting meaningful `custom_id`s. Results aren't order-guaranteed; the `custom_id` is the *only* reliable link from a result back to its input.
5. **Expecting a single batch request to run your *client-side* tool loop.** This is *not* a blanket "no tool use in batch" — tool use, server tools, and multi-turn conversations are all batchable. The real limit is interactivity: a batched request can't pause for *your code* to execute a tool and resume, so a client-side agentic loop with per-turn round-trips doesn't fit inside one batch request. Batch its individual model calls, or run that loop synchronously. (Server-side tools run within a batch just fine.)

The throughline: **batch is for latency-tolerant, non-blocking work, and the `custom_id` is load-bearing.** When a workflow blocks someone, the right answer is the synchronous API even though it costs twice as much.

## Exam focus

This task statement anchors **Scenario 5 (Claude Code for CI)** — the canonical question contrasts a blocking pre-merge check (synchronous) against an overnight technical-debt report (batch). The reliable distractors all reach for batch's discount where latency matters: "switch both workflows to batch with polling," "batch with a timeout fallback to real-time." The correct answer keeps blocking work synchronous and batches only the latency-tolerant job, and it knows results correlate by `custom_id` (so "batch results can't be ordered" is a misconception, not a real constraint).

## References & further reading

- [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) — the Message Batches API end to end: 50% pricing, the 24-hour window and expiry, `processing_status`, polling, and the four result types. The primary reference for this lesson.
- [Create a Message Batch](https://platform.claude.com/docs/en/api/creating-message-batches) — the `requests` array shape: each entry is a `custom_id` plus a `params` payload identical to a synchronous Messages call.
- [Retrieve Message Batch results](https://platform.claude.com/docs/en/api/retrieving-message-batch-results) — streaming results back memory-efficiently and correlating them to inputs by `custom_id`.

## Exam coverage

- **CCAF** — Domain 4 (Prompt Engineering & Structured Output), Task Statement 4.5: Design efficient batch processing strategies.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
