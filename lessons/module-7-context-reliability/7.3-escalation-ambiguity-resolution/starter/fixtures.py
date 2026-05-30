"""Support fixtures for the escalation/ambiguity-resolution exercise.

These ship fully implemented — they are NOT the exercise. The exercise is in
escalation.py. This module gives you a default routing policy and a set of
sample structured signals (the kind of typed data a model would emit via
Structured Outputs) so the tests have realistic inputs to route.

A `signal` is a dict with four keys:
    confidence:        float in [0, 1] — how sure the model is.
    missing_required:  list[str] — names of required fields that are absent.
    ambiguous:         bool — request resolves to more than one thing.
    stakes:            "low" | "high" — cost/irreversibility of the action.

A `policy` is a dict with two thresholds:
    confidence_threshold:     general confidence floor.
    high_stakes_threshold:    stricter floor for high-stakes actions.
"""

# Tuned in the lesson: high-stakes actions face a stricter bar than ordinary ones.
DEFAULT_POLICY = {
    "confidence_threshold": 0.6,
    "high_stakes_threshold": 0.85,
}

# Refund requested but no order id present -> can't proceed.
SIGNAL_MISSING_FIELD = {
    "confidence": 0.9,
    "missing_required": ["order_id"],
    "ambiguous": False,
    "stakes": "high",
}

# Two required fields missing at once.
SIGNAL_MISSING_TWO = {
    "confidence": 0.95,
    "missing_required": ["order_id", "email"],
    "ambiguous": False,
    "stakes": "low",
}

# All fields present, but "the recent order" matches three orders.
SIGNAL_AMBIGUOUS = {
    "confidence": 0.8,
    "missing_required": [],
    "ambiguous": True,
    "stakes": "low",
}

# High-stakes refund; model only 0.7 confident -> below the 0.85 high-stakes bar.
SIGNAL_HIGHSTAKES_LOWCONF = {
    "confidence": 0.7,
    "missing_required": [],
    "ambiguous": False,
    "stakes": "high",
}

# Low-stakes lookup, but confidence 0.5 is below the general 0.6 floor.
SIGNAL_LOWSTAKES_LOWCONF = {
    "confidence": 0.5,
    "missing_required": [],
    "ambiguous": False,
    "stakes": "low",
}

# Complete, unambiguous, confident, low-stakes -> just answer.
SIGNAL_ANSWERABLE = {
    "confidence": 0.95,
    "missing_required": [],
    "ambiguous": False,
    "stakes": "low",
}
