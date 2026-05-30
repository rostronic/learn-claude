"""Starter skeleton for Learn Claude chapter 4.1 — Multi-step workflows with
enforcement & handoff.

Implement `prerequisite_gate` and `record_step` below. See exercise.md for the
full spec. The gate models the Agent SDK PreToolUse hook contract: it receives a
dict describing a requested tool call and returns either {} (allow) or a deny
object. The runtime enforces a deny regardless of how the model was prompted.
"""

# Map each guarded tool to the steps that must complete before it may run.
# Unlisted tools are unguarded (always allowed).
PREREQUISITES = {
    "issue_refund": ["verify_identity", "check_refund_policy"],
}


def prerequisite_gate(input_data: dict, state: dict) -> dict:
    """Decide whether a requested tool call may proceed.

    Args:
        input_data: a PreToolUse-shaped dict, e.g.
            {"hook_event_name": "PreToolUse",
             "tool_name": "issue_refund",
             "tool_input": {"order_id": "A1", "amount": 42.0}}
        state: the workflow handoff state, e.g.
            {"completed": set(), "data": {}}
            `completed` holds the names of steps that have finished;
            `data[step]` holds that step's recorded output.

    Returns:
        {} to ALLOW the call, or a deny object of the exact shape:
            {"hookSpecificOutput": {
                "hookEventName": <input_data["hook_event_name"]>,
                "permissionDecision": "deny",
                "permissionDecisionReason": <human-readable reason>}}
        Deny `issue_refund` until BOTH prerequisites are in `completed` AND the
        recorded policy output (`data["check_refund_policy"]`) has
        `eligible` is True.
    """
    # TODO: implement
    #   1. tool_name = input_data["tool_name"].
    #   2. Look up PREREQUISITES.get(tool_name). If None -> unguarded, return {}.
    #   3. Compute which prerequisites are missing from state["completed"].
    #   4. For issue_refund, also require state["data"]["check_refund_policy"]["eligible"] is True.
    #   5. If anything is missing/ineligible, return the deny object with a
    #      reason naming what's missing. Otherwise return {}.
    #   Do NOT inspect any model/assistant text and do NOT trust a prompt
    #   instruction — the gate is a deterministic check on state.
    raise NotImplementedError("Implement prerequisite_gate — see exercise.md")


def record_step(state: dict, step: str, output: dict) -> dict:
    """Mark a step complete and hand its output off to downstream steps.

    Mutates and returns `state`: adds `step` to state["completed"] and stores
    `output` at state["data"][step] so the gate (and later steps) can read it.
    """
    # TODO: implement
    #   - Ensure state has "completed" (a set) and "data" (a dict).
    #   - Add `step` to completed; set data[step] = output.
    #   - Return state.
    raise NotImplementedError("Implement record_step — see exercise.md")
