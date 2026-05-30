"""Tests for the refund-workflow prerequisite gate and handoff state.

Pure logic — no Anthropic client, no network, no API key needed. The gate is
modelled on the Agent SDK PreToolUse hook contract: a dict in, a decision dict
out.
"""

import pytest

from workflow import prerequisite_gate, record_step
from workflow_steps import check_refund_policy, issue_refund, verify_identity


def _pre(tool_name, **tool_input):
    """Build a PreToolUse-shaped input_data dict for a requested tool call."""
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


def _fresh_state():
    return {"completed": set(), "data": {}}


def _is_deny(decision):
    """True iff `decision` is a well-formed PreToolUse deny object."""
    hso = decision.get("hookSpecificOutput", {})
    return (
        hso.get("hookEventName") == "PreToolUse"
        and hso.get("permissionDecision") == "deny"
        and isinstance(hso.get("permissionDecisionReason"), str)
        and hso["permissionDecisionReason"] != ""
    )


def test_unguarded_tool_is_always_allowed():
    decision = prerequisite_gate(_pre("verify_identity", customer_id="c1"), _fresh_state())
    assert decision == {}


def test_refund_denied_with_no_prerequisites_done():
    decision = prerequisite_gate(_pre("issue_refund", order_id="A1", amount=42.0), _fresh_state())
    assert _is_deny(decision)


def test_refund_denied_with_only_one_prerequisite_done():
    state = _fresh_state()
    record_step(state, "verify_identity", verify_identity("c1"))
    decision = prerequisite_gate(_pre("issue_refund", order_id="A1", amount=42.0), state)
    assert _is_deny(decision)


def test_refund_denied_when_both_done_but_policy_ineligible():
    state = _fresh_state()
    record_step(state, "verify_identity", verify_identity("c1"))
    # $900 order -> policy returns eligible=False
    record_step(state, "check_refund_policy", check_refund_policy("A1", 900.0))
    decision = prerequisite_gate(_pre("issue_refund", order_id="A1", amount=900.0), state)
    assert _is_deny(decision)


def test_refund_allowed_only_when_prereqs_done_and_eligible():
    state = _fresh_state()
    record_step(state, "verify_identity", verify_identity("c1"))
    record_step(state, "check_refund_policy", check_refund_policy("A1", 42.0))
    decision = prerequisite_gate(_pre("issue_refund", order_id="A1", amount=42.0), state)
    assert decision == {}
    # And the guarded step itself still works once allowed.
    assert issue_refund("A1", 42.0)["refunded"] is True


def test_record_step_accumulates_completed_and_hands_off_output():
    state = _fresh_state()
    record_step(state, "verify_identity", verify_identity("c1"))
    record_step(state, "check_refund_policy", check_refund_policy("A1", 42.0))
    assert state["completed"] == {"verify_identity", "check_refund_policy"}
    # The policy output is handed off so the gate can read eligibility.
    assert state["data"]["check_refund_policy"]["eligible"] is True


def test_deny_object_has_exact_hook_shape():
    decision = prerequisite_gate(_pre("issue_refund", order_id="A1", amount=42.0), _fresh_state())
    hso = decision["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert "verify_identity" in hso["permissionDecisionReason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
