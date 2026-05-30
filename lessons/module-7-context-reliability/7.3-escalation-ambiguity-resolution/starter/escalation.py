"""Escalation and ambiguity-resolution triage gate.

Implement the two functions below. Both are pure logic — no API calls, no
network. The signal/policy shapes are documented in fixtures.py.
"""
from typing import List


def route(signal, policy):
    """Deterministic triage gate. Return 'answer', 'clarify', or 'escalate'.

    The decision is an ORDERED gate over the signal's typed fields. Order
    matters: the cheaper, more recoverable action (ask the user) wins over
    the more expensive one (page a human), so missing/ambiguous are checked
    first.

    Args:
        signal: dict with keys confidence (float 0-1), missing_required
                (list[str]), ambiguous (bool), stakes ("low" | "high").
        policy: dict with keys confidence_threshold and high_stakes_threshold.

    Returns:
        'clarify'  if a required field is missing, OR the request is ambiguous;
        'escalate' if high-stakes and confidence < high_stakes_threshold,
                   OR confidence < confidence_threshold;
        'answer'   otherwise (complete, unambiguous, confident enough).
    """
    # TODO 1: If signal["missing_required"] is non-empty, return "clarify".
    # TODO 2: Else if signal["ambiguous"] is True, return "clarify".
    # TODO 3: Else if stakes == "high" AND confidence < policy["high_stakes_threshold"],
    #         return "escalate".
    # TODO 4: Else if confidence < policy["confidence_threshold"], return "escalate".
    # TODO 5: Otherwise return "answer".
    # Keep this exact order — cheaper/recoverable actions (clarify) are checked
    # before the more expensive one (escalate).
    raise NotImplementedError("Implement route()")


def clarifying_question(missing_required):
    """Build a TARGETED clarifying question naming the specific missing fields.

    A targeted question ("To proceed I need: order_id, email.") resolves in one
    turn; a vague one ("Can you clarify?") just earns a second vague reply.

    Args:
        missing_required: list[str] — the names of the missing required fields.

    Returns:
        A string that names each missing field explicitly.
    """
    # TODO 1: Join the field names from missing_required (e.g. with ", ").
    # TODO 2: Return a string that NAMES those specific fields, e.g.
    #         "To proceed I need: order_id, email." — NOT a vague
    #         "Can you clarify?".
    raise NotImplementedError("Implement clarifying_question()")
