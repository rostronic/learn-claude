"""Tests for the escalation/ambiguity triage gate.

Deterministic, no network. Run with: python3 -m pytest -q
"""
from escalation import route, clarifying_question
from fixtures import (
    DEFAULT_POLICY,
    SIGNAL_MISSING_FIELD,
    SIGNAL_MISSING_TWO,
    SIGNAL_AMBIGUOUS,
    SIGNAL_HIGHSTAKES_LOWCONF,
    SIGNAL_LOWSTAKES_LOWCONF,
    SIGNAL_ANSWERABLE,
)


def test_missing_required_clarifies():
    # A missing required field -> clarify, regardless of high confidence/stakes.
    assert route(SIGNAL_MISSING_FIELD, DEFAULT_POLICY) == "clarify"
    assert route(SIGNAL_MISSING_TWO, DEFAULT_POLICY) == "clarify"


def test_ambiguous_clarifies():
    # All fields present but ambiguous -> clarify.
    assert route(SIGNAL_AMBIGUOUS, DEFAULT_POLICY) == "clarify"


def test_high_stakes_low_confidence_escalates():
    # 0.7 confidence is below the 0.85 high-stakes bar -> escalate to a human.
    assert route(SIGNAL_HIGHSTAKES_LOWCONF, DEFAULT_POLICY) == "escalate"


def test_low_stakes_low_confidence_escalates():
    # 0.5 confidence is below the 0.6 general floor -> escalate even at low stakes.
    assert route(SIGNAL_LOWSTAKES_LOWCONF, DEFAULT_POLICY) == "escalate"


def test_confident_complete_unambiguous_answers():
    # Complete, unambiguous, confident, low-stakes -> answer.
    assert route(SIGNAL_ANSWERABLE, DEFAULT_POLICY) == "answer"


def test_high_stakes_confidence_band_is_stricter():
    # The SAME 0.7 confidence that escalates a high-stakes action would answer a
    # low-stakes one (0.7 >= 0.6). The asymmetry is the point.
    low_stakes_same_conf = dict(SIGNAL_HIGHSTAKES_LOWCONF, stakes="low")
    assert route(low_stakes_same_conf, DEFAULT_POLICY) == "answer"


def test_clarifying_question_names_each_missing_field():
    q = clarifying_question(["order_id", "email"])
    assert "order_id" in q
    assert "email" in q


def test_clarifying_question_is_targeted_not_vague():
    # A single missing field is still named explicitly.
    q = clarifying_question(["order_id"])
    assert "order_id" in q
