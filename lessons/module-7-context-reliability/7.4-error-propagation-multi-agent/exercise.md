# Error propagation across multi-agent systems — exercise

## What you're building

Implement `run_pipeline` in `pipeline.py`. It's the coordinator from the lesson: a sequential pipeline of stages (think: subagents) where each stage's result is threaded forward, failures are surfaced as **structured, attributed errors**, transient failures are retried, and one stage's failure must neither crash the run nor corrupt downstream stages.

## Function signature

```python
def run_pipeline(stages, initial_input, max_retries=1):
    """
    Run stages sequentially, threading the previous value forward.

    Args:
        stages:        list of (name, fn) tuples. Each fn(input) returns a dict:
                         {"ok": True,  "value": <result>}                    on success
                         {"ok": False, "error": <str>, "transient": <bool>}  on failure
        initial_input: the value passed to the first stage's fn.
        max_retries:   how many EXTRA times to re-run a stage whose failure is
                       transient. Non-transient failures are never retried.

    Returns:
        {
          "status": "ok" | "failed",
          "results": [ {"stage": <name>, "value": <value>}, ... ],   # successes, in order
          "errors":  [ {"stage": <name>, "error": <str>, "recoverable": <bool>}, ... ],
        }
    """
```

## Requirements

You must:

1. **Run stages in order, threading the value forward.** A successful stage's `"value"` becomes the next stage's input. Record each success as `{"stage": name, "value": value}` in `results`.
2. **Retry transient failures only.** If a stage returns `{"ok": False, "transient": True, ...}`, re-run it up to `max_retries` extra times. If a retry succeeds, continue normally.
3. **Surface failures as structured, attributed errors.** On a non-transient failure (or a transient one that exhausts its retries), append `{"stage": name, "error": <the stage's instructive message>, "recoverable": <bool from transient>}` to `errors`. The `stage` field is the provenance — *which* stage failed.
4. **Stop on a hard failure, and never thread a missing value forward.** When a stage fails for good, return `{"status": "failed", ...}` immediately. Downstream stages must NOT run, and the failed stage's (missing) value must NEVER be passed to the next stage.
5. **Pass every test in `test_pipeline.py`.**

You must NOT:

6. **Swallow the error.** Do not catch a failure and return a success-shaped value (e.g. `return None`, `{}`, or an empty result) as if the stage had succeeded. A failed stage must produce a non-empty `errors` entry with its provenance — never a silent success. This is graded directly (`check: anti_pattern`).
7. **Crash the whole run on one stage's failure.** `run_pipeline` must never raise on a stage failure; it always returns the structured aggregate. One stage failing is contained, not fatal.

## How to run it

```bash
cd ~/learn-claude-work/7.4
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — fake stage functions in `fixtures.py` stand in for subagents. No `ANTHROPIC_API_KEY`, no network, no API credits.

When you're ready (or stuck), run `/verify 7.4` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — `is_error` and instructive error messages ("what went wrong and what to try next"); the tool-boundary version of what you're building.
- [Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — why only a subagent's final message returns to the parent, which is why a swallowed failure is invisible.
