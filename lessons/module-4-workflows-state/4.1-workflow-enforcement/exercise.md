# Multi-step workflows with enforcement & handoff — exercise

## What you're building

A **prerequisite gate** and the **handoff** that feeds it, for a support-refund
workflow. `issue_refund` must not run until both `verify_identity` and
`check_refund_policy` have completed *and* the policy came back eligible. You
implement the gate as a pure function modelled on the Agent SDK `PreToolUse`
hook contract — a dict in, an allow/deny decision out — plus `record_step`, the
handoff that records each finished step's output into shared state.

## Function signatures

```python
PREREQUISITES = {"issue_refund": ["verify_identity", "check_refund_policy"]}

def prerequisite_gate(input_data, state):
    """
    input_data: a PreToolUse-shaped dict:
        {"hook_event_name": "PreToolUse",
         "tool_name": <str>,
         "tool_input": {...}}
    state: workflow handoff state: {"completed": set[str], "data": {step: output}}

    Returns {} to ALLOW, or a deny object:
        {"hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "deny",
            "permissionDecisionReason": <str naming what's missing>}}
    """

def record_step(state, step, output):
    """Mark `step` complete and store `output` at state["data"][step]. Returns state."""
```

## Requirements

You must:

1. **Allow unguarded tools.** If `tool_name` is not in `PREREQUISITES`, return `{}`.
2. **Deny a guarded call whose prerequisites are not all in `state["completed"]`,** with a reason that names the missing step(s).
3. **For `issue_refund`, additionally require** the handed-off policy output (`state["data"]["check_refund_policy"]`) to have `eligible` is `True`; deny otherwise.
4. **Return the exact deny shape** (`hookSpecificOutput` → `hookEventName`/`permissionDecision`/`permissionDecisionReason`), and `{}` when the call is allowed.
5. **Implement `record_step`** so it adds to `state["completed"]` and stores the output in `state["data"]`, making it available to the gate.
6. **Pass every test in `test_workflow.py`.**

You must NOT:

7. **Decide based on model/assistant text or a prompt instruction.** The gate is a deterministic check on `state` only. No reading of conversation text, no "the model said it verified" — if your gate's verdict depends on anything other than recorded state, you've built the wrong thing.
8. **Let the guarded call through and "check after."** The gate must return `deny` *before* the action runs when prerequisites aren't met — not run `issue_refund` and undo it.

Requirements 7 and 8 are graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/4.1
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — no Anthropic client, no `ANTHROPIC_API_KEY`, no API
credits. To wire your gate into a real agent afterward, register
`prerequisite_gate` as a `PreToolUse` hook (`pip install claude-agent-sdk`) with
`HookMatcher(matcher="issue_refund", hooks=[...])`; the decision logic is
unchanged.

When you're ready (or stuck), run `/verify 4.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Agent SDK — hooks](https://code.claude.com/docs/en/agent-sdk/hooks) — the `PreToolUse` `permissionDecision`/`permissionDecisionReason` shape your gate returns, and the rule that a `deny` blocks the call.
- [Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — why state must be handed off explicitly, not assumed.
