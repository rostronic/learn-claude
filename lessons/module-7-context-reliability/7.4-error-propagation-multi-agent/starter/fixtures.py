"""Fake stage functions for exercising run_pipeline.

Every stage function has the signature fn(input) -> dict and returns a result
dict shaped like the API our pipeline expects:

    {"ok": True,  "value": <result>}                       # success
    {"ok": False, "error": <str>, "transient": <bool>}     # failure

These are deterministic test doubles for what would otherwise be a subagent or
tool call. No network, no Anthropic SDK — pure logic so the tests run offline.
"""


def ok_stage(name, transform=None):
    """Build a stage fn that always succeeds.

    If `transform` is given it maps the incoming value to the outgoing value;
    otherwise the stage appends its own name to a running list so tests can
    assert ordering and that the previous value was threaded forward.
    """

    def _fn(value):
        if transform is not None:
            return {"ok": True, "value": transform(value)}
        chain = list(value) if isinstance(value, list) else [value]
        chain.append(name)
        return {"ok": True, "value": chain}

    return _fn


def transient_then_ok(name, fail_times=1):
    """Build a stage fn that fails transiently `fail_times` times, then succeeds.

    Uses a mutable closure counter so retries within a single run_pipeline call
    eventually succeed. Each instance is independent.
    """
    state = {"calls": 0}

    def _fn(value):
        state["calls"] += 1
        if state["calls"] <= fail_times:
            return {
                "ok": False,
                "error": "Upstream timed out after 30s. Retry shortly.",
                "transient": True,
            }
        chain = list(value) if isinstance(value, list) else [value]
        chain.append(name)
        return {"ok": True, "value": chain}

    return _fn


def hard_fail_stage(name, error="Invalid input: schema validation failed"):
    """Build a stage fn that always fails non-transiently (no retry will help)."""

    def _fn(value):
        return {"ok": False, "error": error, "transient": False}

    return _fn
