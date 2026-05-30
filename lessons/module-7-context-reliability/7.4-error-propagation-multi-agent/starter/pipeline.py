"""Error propagation across a multi-stage agent pipeline.

Implement run_pipeline: a sequential coordinator that threads each stage's
result forward, surfaces failures as structured/attributed errors, retries
transient failures, and never raises.
"""


def run_pipeline(stages, initial_input, max_retries=1):
    """Run stages sequentially, threading the previous value forward.

    Args:
        stages:        list of (name, fn) tuples. Each fn(input) returns a dict:
                         {"ok": True,  "value": <result>}                    on success
                         {"ok": False, "error": <str>, "transient": <bool>}  on failure
        initial_input: the value passed to the first stage's fn.
        max_retries:   how many EXTRA times to re-run a stage whose failure is
                       transient (transient is True). Non-transient failures are
                       never retried.

    Behavior:
        - A successful stage's "value" becomes the next stage's input.
        - A transient failure is retried up to max_retries times; if a retry
          succeeds the pipeline continues normally.
        - A non-transient failure (or a transient one that exhausts its retries)
          STOPS the pipeline: downstream stages do NOT run, and the failed
          stage's (missing) value is NEVER threaded forward.
        - The function NEVER raises on a stage failure; it returns an aggregate.

    Returns:
        {
          "status": "ok" | "failed",
          "results": [ {"stage": <name>, "value": <value>}, ... ],   # successes, in order
          "errors":  [ {"stage": <name>, "error": <str>, "recoverable": <bool>}, ... ],
        }
        On success "errors" is empty; on failure "errors" carries exactly the
        failing stage (provenance) with its instructive message, and
        "recoverable" reflects whether the failure was transient.
    """
    # TODO 1: Set up the aggregate accumulators (results, errors) and a
    #         `current` value seeded from initial_input. Iterate (name, fn) pairs
    #         in order.
    # TODO 2: For each stage, run fn(current). Retry ONLY when the failure is
    #         transient (outcome.get("transient") is True) and you have budget
    #         left, up to max_retries EXTRA attempts. Never retry a non-transient
    #         failure.
    # TODO 3: On success, thread the value forward: set current = outcome["value"]
    #         and append {"stage": name, "value": current} to results. Continue.
    # TODO 4: On failure (non-transient, or transient after exhausting retries),
    #         append a STRUCTURED, ATTRIBUTED error to errors:
    #         {"stage": name, "error": <instructive message from outcome>,
    #          "recoverable": bool(outcome.get("transient", False))}.
    #         Then STOP: return {"status": "failed", ...} immediately. Do NOT run
    #         downstream stages and do NOT thread the missing value forward.
    # TODO 5: If every stage succeeded, return {"status": "ok", "results": ...,
    #         "errors": []}. Never raise on a stage failure.
    raise NotImplementedError("Implement run_pipeline (see the TODOs above).")
