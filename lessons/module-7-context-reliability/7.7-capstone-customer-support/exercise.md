# Capstone — Customer Support Resolution Agent — exercise

## What you're building

This capstone has no code to run — it's a **design exercise**. You'll write an architecture document for the Customer Support Resolution Agent from the lesson and defend the five decisions that make or break it. The verifier grades your written reasoning, not a test suite.

Write your design to:

```
~/learn-claude-work/7.7/design.md
```

Create the directory if it doesn't exist (`mkdir -p ~/learn-claude-work/7.7`). One markdown file; no starter to copy.

## The scenario

A customer support agent investigates tickets across four tools — order lookup, payment-processor status, shipping-carrier tracking, and knowledge-base search — over a thread that can run dozens of messages. It resolves tickets it can handle and routes the rest to a human. Business rules: refunds over \$200 need human approval; account closures and chargeback disputes always need a human. The resolution feeds a ticketing system that executes the refund automatically, so the output has to be machine-ingestible and the controls have to hold every time.

## What your design.md must specify

Address each of these five sections explicitly. For each, state the decision *and the reason it's correct on this exam* — don't just assert it.

1. **Loop termination.** How the investigation loop knows it's done. Name the exact signal you dispatch on and say what role (if any) a turn cap plays. State plainly what you are *not* using as the termination signal and why.

2. **Context strategy for the long thread.** How the agent stays accurate and under the limit as the thread grows to dozens of messages. Cover the token budget, summarization of older turns, and a durable scratchpad for the load-bearing facts (order ID, disputed amount, customer tier, what's been tried). Explain the division of labor between summarization and the scratchpad.

3. **Programmatic escalation gate.** The concrete rules that route an action to a human, and *where* those rules live. Give at least the \$200 refund rule and one always-escalate action. Make clear the enforcement is in code the action passes through, not an instruction the model is asked to follow.

4. **Confidence-based human handoff.** How a low-confidence field gets routed to a person, distinct from the action-based gate. Cover where the confidence signal comes from and how the threshold relates to the cost of being wrong for that field. Say who reviews a low-confidence field.

5. **Structured resolution schema.** The schema of the resolution record the agent emits, and how you guarantee it's valid. List the fields (at minimum: disposition, the proposed/executed action, confidence, a handoff flag + reason, and an evidence/grounding trail) and name the mechanism that makes the JSON always-valid.

Keep it concrete — a senior engineer should be able to read your `design.md` and build the agent from it.

## What your design must NOT do

The rubric grades these as anti-patterns. Your design fails the relevant criterion if it:

- Uses **text-parsing** ("stop when the reply says 'anything else?'") or an **iteration/turn cap** as the loop's *termination signal*. (A cap as a pure runaway guard is fine — but it must not be how the loop decides it's done.)
- Relies on a **prompt instruction** ("tell the model never to refund over \$200") as the *enforcement* of the refund limit or any other deterministic business rule.

If either appears as your chosen approach, you'll lose those points whether or not the rest of the design is strong.

## When you're done

Run `/verify 7.7` and I'll grade your design against the rubric, then point you at the next chapter or any decision worth revisiting.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — `stop_reason` and the `max_turns` guard.
- [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows) and [Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) — the long-thread context strategy.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — the always-valid resolution record.
