---
chapter: "7.7"
slug: "capstone-customer-support"
title: "Capstone — Customer Support Resolution Agent"
module: "module-7-context-reliability"
sequence: 34
references:
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs
    covers: "Loop lifecycle, stop_reason as the termination signal, max_turns safety cap"
  - title: "Context windows"
    url: "https://platform.claude.com/docs/en/build-with-claude/context-windows"
    type: official_docs
    covers: "Progressive token accumulation, context rot, overflow stop_reason on a long ticket thread"
  - title: "Memory tool"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool"
    type: official_docs
    covers: "Client-side scratchpad files that persist ticket state across a long thread / sessions"
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "Say 'I don't know', ground in quotes, ask for clarification — confidence inputs for handoff"
  - title: "Increase consistency"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency"
    type: official_docs
    covers: "Specify output format; ask before proceeding when unsure"
  - title: "Structured outputs"
    url: "https://platform.claude.com/docs/en/build-with-claude/structured-outputs"
    type: official_docs
    covers: "Guaranteed schema-compliant JSON for the resolution record"
---

# Capstone — Customer Support Resolution Agent

## Overview

This is the first CCA-F exam scenario, and it's the one that exercises the most of Domain 5 at once: a **Customer Support Resolution Agent**. The product brief is mundane and the engineering is not. A customer opens a ticket ("my refund never arrived"), the agent investigates across tools — order lookup, payment processor, shipping carrier, the knowledge base — and either resolves the ticket itself or routes it to a human. It has to do this over a thread that can run dozens of messages, while never refunding more money than it's allowed to and never confidently asserting something it can't substantiate.

Nothing in this capstone is new mechanism — you've met every piece in Modules 3 and 7. What's new is the *integration*: five separate decisions that each have a single correct answer on this exam, wired into one agent where a wrong call on any of them sinks the whole thing. The five:

1. **Knowing when investigation is done** — the agentic loop terminates on `stop_reason`, never on parsed text or a turn count (Task Statement 1.1).
2. **Surviving a long ticket thread** — a token budget plus summarization plus a durable scratchpad keep the critical facts in context as the thread grows (Task Statement 5.1).
3. **A programmatic escalation gate** — high-value refunds and other high-stakes actions route to a human via *code*, not via a sentence in the prompt (Task Statement 5.2).
4. **Confidence-based human handoff** — when the agent's confidence in a field is low, that field goes to a person, calibrated against the cost of being wrong (Task Statement 5.5).
5. **Emitting the resolution as structured output** — the final resolution record is schema-constrained JSON your ticketing system can ingest without a parser babysitter (Task Statement 4.3).

We'll architect all five end-to-end, then you'll write the design doc in the exercise.

## How it works

### 1. The investigation loop terminates on `stop_reason`

The agent's outer control flow is the agentic loop from chapter 3.1: the model evaluates the prompt, calls tools to take action, receives the results, and repeats until the task is complete ([Agent SDK — agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)). The support agent calls the model with its tools (order lookup, payment status, shipping, KB search), and the model either requests a tool or finishes. Because this capstone drives the raw Messages API directly (not the Agent SDK wrapper), it dispatches on the Messages-API `stop_reason` shape: the loop continues while `stop_reason == "tool_use"` and exits when `stop_reason == "end_turn"`.

The temptation specific to a *support* agent is to terminate on the prose. The model writes "I've confirmed the refund was processed on the 3rd — is there anything else I can help with?" and it's so obviously a closing line that string-matching it feels safe. It isn't. The model phrases closings a hundred ways, and it routinely narrates mid-investigation ("Let me check the carrier's tracking…") in the *same* turn as a `tool_use` block. Dispatch on `stop_reason`; keep a `max_turns`-style cap purely as a runaway guard ([Agent SDK — agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)).

```python
def investigate(client, messages, tools, run_tool, max_turns=25):
    for _ in range(max_turns):                 # runaway guard, NOT the exit
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=4096,
            tools=tools, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "end_turn":
            return resp                         # the only real exit
        if resp.stop_reason == "tool_use":
            results = []
            for block in resp.content:
                if block.type == "tool_use":
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": run_tool(block.name, block.input),
                    })
            messages.append({"role": "user", "content": results})
            continue
        raise RuntimeError(f"unexpected stop_reason: {resp.stop_reason}")
    raise RuntimeError("hit max_turns without end_turn")
```

### 2. Surviving the long ticket thread

A real support ticket is not three messages. The customer replies, the agent re-investigates, escalation bounces it back, a week passes. Every turn accumulates: "the system prompt, tool definitions, conversation history, tool inputs, and tool outputs" all pile up, and the API will eventually refuse the request with `stop_reason: "model_context_window_exceeded"` ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). Worse than the hard ceiling is the soft one: **context rot** — accuracy degrades as the token count climbs, even well under the limit ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). A 60-message thread where the order ID is buried in message 4 is a thread where the agent quietly starts getting the order ID wrong.

The architecture has two moving parts:

- **A token budget with summarization.** You track the thread's token count and, past a threshold, replace the older turns with a concise summary, keeping the recent turns verbatim. Separately, Sonnet and Haiku models have a built-in context-awareness feature: the model automatically *receives* its remaining token budget via injected `<budget:token_budget>` and `<system_warning>` signals, which lets it wrap up rather than overflow — this is supplied by the platform, not hand-injected by the integrator ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)).
- **A durable scratchpad via the memory tool.** Summarization is lossy by design, so the load-bearing facts — order ID, customer tier, the refund amount under dispute, what's already been tried — get written to a memory file the moment they're established. The memory tool is a "client-side file directory (`/memories`) Claude can create, read, update, and delete to persist information across sessions without keeping it in context"; "memory persists important information across compaction boundaries" ([Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)). When the thread is summarized — or resumed days later — the agent reads the scratchpad back and recovers the ground truth instead of trusting a summary that may have dropped the refund amount.

The division of labor is the point: **summarization keeps the conversation small; the scratchpad keeps the critical facts exact.** Neither alone is enough. Summaries lose precision; an ever-growing verbatim thread rots.

### 3. The programmatic escalation gate

Some actions are too consequential to leave to a prompt. "Refund more than \$200 must be approved by a human" is a business rule that requires *deterministic* compliance, and the Anthropic-prescribed way to enforce a rule like that is in code — a gate the agent's action must pass through — not a sentence in the system prompt. A prompt instruction ("never refund over \$200 without approval") is a strong suggestion the model usually follows; it is not a guarantee, and "usually" is not a control you can put in front of an auditor.

So the agent never issues a refund directly. It *proposes* one, and the proposal is checked by a pure function before any money moves:

```python
def escalation_gate(action):
    """Returns 'auto' if the agent may execute, else a human-routing reason.
    Deterministic: same action in -> same decision out."""
    if action["type"] == "refund" and action["amount_usd"] > 200:
        return "escalate: refund exceeds $200 auto-approval limit"
    if action["type"] in ("account_closure", "chargeback_dispute"):
        return "escalate: high-stakes action requires human review"
    return "auto"
```

This is the same lesson as hooks and prerequisite gates elsewhere on the exam: **programmatic enforcement over prompt instructions for any rule that must hold deterministically.** The gate doesn't ask the model nicely — it intercepts the proposed action and routes it. The model can be told about the limit too (it makes for better proposals), but the *enforcement* lives in the function, where it can't be talked out of.

### 4. Confidence-based human handoff

The escalation gate keys off the *action*; the handoff keys off the agent's *confidence*. These are different axes. A \$15 refund the agent is sure about sails through. A \$15 refund where the agent isn't sure the order even shipped should still see a human, because being wrong is expensive relative to the amount.

The confidence inputs come straight from the reliability guardrails. The agent is instructed to **say "I don't know" rather than guess**, to **ground claims in direct quotes** from the order record or KB before asserting them, and to **ask for clarification when information is missing** ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)); "if unsure, ask for clarification before proceeding" ([Increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)). Those produce a per-field signal — an explicit confidence, or a sourced/unsourced flag — and the handoff is calibrated against the **cost of an error in that field**, not a single global threshold:

```python
def needs_human(field, confidence, cost_if_wrong):
    # Low confidence on a cheap field is fine; on a costly field it isn't.
    threshold = 0.95 if cost_if_wrong == "high" else 0.70
    return confidence < threshold
```

The expensive fields (refund eligibility, account actions) demand near-certainty; the cheap fields (which help-center article to link) tolerate more doubt. A field below its threshold is handed to a person *for that field* — the rest of the resolution can still proceed.

### 5. The resolution as structured output

When the agent finishes, it emits a **resolution record**, not prose. That record feeds the ticketing system, drives metrics, and triggers the actual refund — so it must be valid every single time. Use Structured Outputs to guarantee schema-compliant JSON via constrained decoding (`output_config.format` with `type: "json_schema"`): "Always valid: No more JSON.parse() errors" ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)). The schema makes the fields above first-class:

```json
{
  "ticket_id": "T-48213",
  "disposition": "resolved",
  "action": { "type": "refund", "amount_usd": 42.50 },
  "confidence": 0.97,
  "handoff_required": false,
  "handoff_reason": null,
  "evidence": ["order O-991 status=delivered", "payment P-771 refunded 2026-05-03"]
}
```

`disposition` is an enum (`resolved` / `escalated` / `needs_human`), `handoff_required` is a boolean the downstream router branches on, and `evidence` is the grounding trail — the quotes the agent based its decision on, so a human reviewer can audit it. Schema-constrained output means the router never has to defend against a missing field or a stray code-fence.

## Worked example

Put the five pieces in series and the agent's lifecycle for one ticket reads top to bottom:

1. **Seed context + scratchpad.** Load the ticket, write `ticket_id`, `customer_tier`, and `disputed_amount` to a memory file ([Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)).
2. **Investigate.** Run `investigate(...)` — the loop calls order-lookup, payment-status, shipping, KB-search as the model requests them, terminating on `end_turn` ([Agent SDK — agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)). As facts are confirmed, they're appended to the scratchpad.
3. **Watch the budget.** Each turn, check the token count; past the threshold, summarize the older turns and keep the recent ones, then re-read the scratchpad so no confirmed fact is lost to the summary ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)).
4. **Propose, then gate.** The model proposes an action with a per-field confidence. `escalation_gate(action)` runs first — a \$420 refund returns `"escalate: refund exceeds $200…"` regardless of how confident the model is. If the gate says `auto`, `needs_human(field, confidence, cost)` runs per field; refund-eligibility below 0.95 still pulls in a human.
5. **Emit.** Build the resolution record as schema-constrained JSON ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)). `disposition` is `resolved` only if the gate passed and no field needed a human; otherwise `escalated` or `needs_human`, with `handoff_reason` filled and `evidence` carrying the grounding quotes.

Trace two tickets through it. **Ticket A:** "\$42 refund, order shows delivered then returned." Investigation confirms the return (high confidence, grounded in the carrier record), the gate passes (\$42 < \$200), no field is below threshold → `disposition: resolved`, refund executes, record emitted. **Ticket B:** "\$420 refund for a damaged item." Same investigation, but `escalation_gate` returns `escalate` on the amount before any confidence check matters → `disposition: escalated`, `handoff_required: true`, `action` proposed-not-executed, evidence attached for the human. The two tickets differ only in the amount, and the *code path*, not the prompt, is what diverges them.

## Anti-patterns & pitfalls

The distractors this scenario offers are exactly the wrong answer to each of the five decisions:

1. **Terminating the investigation on text or a turn count.** "Stop when the reply contains 'anything else?'" or "stop after 6 turns." Both substitute a proxy for the protocol signal. The model narrates while still calling tools and phrases closings unpredictably; a turn cap declares victory mid-investigation. **Dispatch on `stop_reason`; the cap is only a runaway guard** ([Agent SDK — agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)).
2. **Letting the thread grow unbounded.** "Modern context windows are huge, just keep appending." This walks straight into context rot and eventually `model_context_window_exceeded` ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). Budget and summarize, and pin the critical facts in a scratchpad ([Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)) — a summary alone will eventually drop the refund amount.
3. **Enforcing the refund limit in the prompt.** "Tell the model never to refund over \$200." This is the headline trap of the whole scenario. A prompt instruction is not a deterministic control; the model will occasionally exceed it, and you cannot prove to an auditor that it won't. **The limit must be a code gate the action passes through** — programmatic enforcement over prompt instructions, every time a rule must hold deterministically.
4. **A single global confidence threshold (or self-grading the final answer).** One cutoff for every field ignores that fields differ wildly in the cost of being wrong; cheap fields get over-escalated and expensive ones under-escalated. Calibrate the threshold to the cost of an error per field. And note the cousin trap from Domain 4: having the *same* agent grade its own resolution — independent review beats self-review, so route low-confidence fields to a human (or a separate reviewer), not back to the author.
5. **Returning the resolution as free-form prose for downstream parsing.** Then someone writes a regex against the model's wording and it breaks the first time the phrasing shifts. **Use Structured Outputs for guaranteed schema-compliant JSON** ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)); the ticketing system ingests it directly.

## Exam focus

This is the canonical Domain 5 scenario, and it's deliberately a junction: a single mock-exam question can hand you a plausible-but-wrong answer for *any* of the five decisions. The reliable tells:

- Loop termination → the option naming `stop_reason`, not the one matching a phrase or counting turns.
- Refund / high-stakes limit → the option that puts the check in **code**, not the one that puts it in the **prompt**.
- Long thread → the option that budgets + summarizes + persists to a scratchpad, not "the window is big enough."
- Confidence → the option that calibrates per field cost and routes to a **human/independent** reviewer, not a single threshold or self-grading.
- Output → the option using Structured Outputs, not prose-plus-parser.

When two options both "work," the exam wants the one that holds **deterministically** and **auditably** — that's the through-line of every decision in this scenario.

## References & further reading

- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — the investigation loop, `stop_reason` as the only termination signal, and `max_turns` as the runaway guard.
- [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows) — progressive token accumulation, context rot, budget-awareness signals, and the `model_context_window_exceeded` overflow on a long ticket thread.
- [Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) — the `/memories` scratchpad that persists the load-bearing ticket facts across summarization and across sessions.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — say "I don't know", ground in quotes, ask when info is missing: the inputs to the confidence signal.
- [Increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — specify the output format and ask before proceeding when unsure.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — guaranteed schema-compliant JSON for the resolution record.

## Exam coverage

- **CCAF** — Scenario 1: Customer Support Resolution Agent. This capstone ties together Task Statements 1.1, 4.3, 5.1, 5.2, and 5.5.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
