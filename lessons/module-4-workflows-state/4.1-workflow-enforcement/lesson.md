---
chapter: "4.1"
slug: "workflow-enforcement"
title: "Multi-step workflows with enforcement & handoff"
module: "module-4-workflows-state"
sequence: 12
references:
  - title: "Agent SDK — Intercept and control agent behavior with hooks"
    url: "https://code.claude.com/docs/en/agent-sdk/hooks"
    type: official_docs
    covers: "PreToolUse fires before a tool runs and can block it; permissionDecision deny + reason; deny is hard-enforced; HookMatcher registration"
  - title: "Agent SDK — Subagents in the SDK"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Handoff: the only channel to a subagent is the prompt string, so required state must be passed explicitly"
---

# Multi-step workflows with enforcement & handoff

## Overview

Most real agent tasks are not one action — they're a *sequence* with rules between the steps. Verify the customer before issuing a refund. Run the linter before opening the PR. Get a manager's approval before deleting the record. The interesting engineering question is not "can the agent do each step" but "**how do you guarantee step N can't happen until step N-1 has actually happened**" — even when the model is confused, adversarially prompted, or just wrong.

There are two ways to encode that rule, and this exam is opinionated about which is correct:

- **Tell the model in the prompt** — "Always verify identity before issuing a refund." This is a *request*. The model usually complies, but compliance is probabilistic: a long conversation, a cleverly worded user message, or a hallucinated assumption can route around it. You cannot prove it holds.
- **Enforce it programmatically** — a deterministic gate that sits in front of the guarded action and blocks it unless the prerequisites are provably satisfied. The model can *ask* for the refund all it wants; the gate refuses to let the call through.

For any business rule that requires deterministic compliance, the prescribed approach is the second one: **programmatic enforcement (hooks, prerequisite gates) over prompt instructions.** A prompt instruction is the wrong tool when "it mostly works" isn't good enough — and for money movement, deletions, and approvals, it never is. This lesson builds the gate, and the handoff of state between steps that the gate depends on.

## How it works

The enforcement point is a **prerequisite gate**: code that runs *before* a guarded tool executes, inspects the workflow's state, and returns one of two verdicts — allow, or deny-with-a-reason. The Agent SDK gives you exactly this seam in the form of a **`PreToolUse` hook**, which "fires before a tool is called" and "can block or modify" it ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). Your callback returns a decision, and crucially, a denial is not advisory: "If any hook returns `deny`, the operation is blocked regardless of other hooks" ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). That sentence is the whole reason to prefer a gate over a prompt — the runtime, not the model, makes the final call.

A `PreToolUse` hook is registered against a tool-name matcher and returns its verdict inside `hookSpecificOutput`:

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

async def refund_gate(input_data, tool_use_id, context):
    # input_data carries the requested tool call: hook_event_name, tool_name, tool_input
    if not refund_prerequisites_met(STATE):
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "deny",
                "permissionDecisionReason": "Identity unverified or policy not checked.",
            }
        }
    return {}  # allow

options = ClaudeAgentOptions(
    hooks={"PreToolUse": [HookMatcher(matcher="issue_refund", hooks=[refund_gate])]},
)
```

`permissionDecision` is a small enum — `"allow"`, `"deny"`, `"ask"`, or `"defer"` — and `permissionDecisionReason` is fed back to the model so it understands *why* it was blocked and doesn't blindly retry ([Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)). Returning `{}` allows the call unchanged. Note the gate dispatches on **state**, never on what the model said — the decision is a pure function of "have the prerequisites actually completed," which is the property that makes it deterministic.

### Handoff: the state the gate reads

A gate is only as good as the state it consults, and that state has to be *populated* by the earlier steps — this is the **handoff**. When `check_refund_policy` runs, its result (`eligible: true/false`) has to be recorded somewhere the gate can later read it. Within a single agent you keep a workflow-state object and write each step's output into it as the step completes; the gate reads that object.

Handoff matters most when a step is delegated to a **subagent**, because a subagent's context starts fresh. The SDK is explicit that almost nothing crosses the boundary automatically: "The only channel from parent to subagent is the Agent tool's prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). So you can't *assume* a downstream step "remembers" that identity was verified — you have to hand the relevant facts forward explicitly, whether that's into a shared state dict (same agent) or into the prompt string (subagent). The gate then enforces against that handed-off state.

## Worked example

Here is the pattern end to end for a support-refund workflow: `issue_refund` must not run until both `verify_identity` and `check_refund_policy` have completed, *and* the policy must have come back eligible. The state object is the handoff medium; the gate is the enforcement.

```python
PREREQUISITES = {"issue_refund": ["verify_identity", "check_refund_policy"]}


def record_step(state, step, output):
    """Handoff: a finished step writes its result where later steps can read it."""
    state.setdefault("completed", set()).add(step)
    state.setdefault("data", {})[step] = output
    return state


def prerequisite_gate(input_data, state):
    """Enforcement: block a guarded call until its prerequisites hold."""
    tool_name = input_data["tool_name"]
    prereqs = PREREQUISITES.get(tool_name)
    if prereqs is None:
        return {}  # unguarded tool — nothing to enforce

    reasons = []
    missing = [p for p in prereqs if p not in state.get("completed", set())]
    if missing:
        reasons.append("missing prerequisite step(s): " + ", ".join(missing))
    if tool_name == "issue_refund":
        policy = state.get("data", {}).get("check_refund_policy", {})
        if not policy.get("eligible", False):
            reasons.append("refund policy not satisfied (eligible is not True)")

    if reasons:
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "deny",
                "permissionDecisionReason": "; ".join(reasons),
            }
        }
    return {}
```

Walking through it:

- **The gate is a pure function of `state`.** It never looks at the assistant's text or trusts that "the model said it verified the customer." It checks the recorded facts. That is what makes the rule provable.
- **`record_step` is the handoff.** `verify_identity` finishing puts `"verify_identity"` in `completed`; `check_refund_policy` finishing stores its `{"eligible": ...}` payload in `data` where the gate reads it. Skip the handoff and the gate can never see the prerequisite as met — the rule and the state are two halves of one mechanism.
- **Deny carries a reason.** The model is told what's missing, so its next move is to *go do the missing step*, not to retry the same blocked call.
- **Wiring it into a real agent** is just registering `prerequisite_gate` as a `PreToolUse` hook with `matcher="issue_refund"` (the snippet in "How it works"), with `state` living in your application. The logic above is identical; only the plumbing differs.

The exercise has you implement exactly this `prerequisite_gate` and `record_step`.

## Anti-patterns & pitfalls

1. **Putting the rule only in the prompt.** "System prompt: always verify identity before issuing a refund." This is the single most tempting wrong answer on this exam, because it *usually works* in a demo. But a prompt instruction is a probabilistic request, not a guarantee — a long context, an injected user instruction, or a model mistake can bypass it, and you can never prove it holds. For a rule that must *always* hold, the model must be structurally unable to skip it. The gate makes skipping impossible; the prompt only makes it unlikely. On this exam, "instruct the model to always X" is wrong wherever deterministic compliance is required.

2. **Checking inside the guarded action, after the model already chose to call it.** Putting an `if not verified: return error` at the top of `issue_refund` is better than nothing, but it's the wrong seam: the rule is now scattered into each action, the call has already been dispatched, and a second guarded action needs its own copy of the check. A `PreToolUse` gate centralizes the rule in front of the call and blocks it *before* execution — one enforcement point the model cannot route around.

3. **Implicit handoff — hoping the model "remembers."** Relying on the conversation text to carry "identity was verified" forward, instead of recording it in state. This fails outright across a subagent boundary, where the child receives nothing but the prompt string ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)) — no parent history, no prior tool results. Hand required state forward explicitly; don't assume continuity that the platform doesn't provide.

All three share the same root error as the loop anti-patterns from earlier in this module: trusting the model's *behavior* where a *deterministic mechanism* is available. **The Anthropic way is to enforce business rules in code and hand state forward explicitly** — not to ask the model nicely and hope.

## Exam focus

This task statement shows up wherever a scenario has an ordering or approval rule that "must" hold:

- **Customer Support Resolution** — refunds, account changes, and escalations gated on identity verification and policy checks.
- **Developer Productivity** — "run tests / get review before merge" style gates over a Claude Code workflow.

The reliable tell: when a question describes a rule that must hold *every* time, the correct answer is a programmatic gate (a `PreToolUse` hook / prerequisite check), and the distractors are some flavor of "instruct the model to," "add a few-shot example showing the right order," or "check after the fact." Pick the mechanism the runtime enforces.

## References & further reading

- [Agent SDK — Intercept and control agent behavior with hooks](https://code.claude.com/docs/en/agent-sdk/hooks) — `PreToolUse` blocking, the `permissionDecision`/`permissionDecisionReason` shape, and the rule that a single `deny` blocks the operation regardless of other hooks. The mechanism this lesson's gate plugs into; covered in depth in the next chapter.
- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — what a subagent does and does not inherit, and why state must be handed off explicitly through the prompt string rather than assumed.

## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.4: Implement multi-step workflows with enforcement and handoff patterns.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
