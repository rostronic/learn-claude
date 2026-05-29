---
lesson_id: "1.1"
task_statement: "1.1 Design and implement agentic loops for autonomous task execution"
exam_guide_reference: "Domain 1, Task Statement 1.1"
references:
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs
    covers: "Loop lifecycle, turns, tool execution, stop_reason, max_turns/budget"
  - title: "How Claude Code works — The agentic loop"
    url: "https://code.claude.com/docs/en/how-claude-code-works"
    type: official_docs
    covers: "The conceptual agentic loop that powers Claude Code and the SDK"
  - title: "Messages API — tool use"
    url: "https://platform.claude.com/docs/en/build-with-claude/tool-use"
    type: official_docs
    covers: "Raw tool_use / tool_result message shapes and stop_reason values"
  - title: "CCA-F Exam Guide — Domain 1, Task Statement 1.1"
    url: "https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F8lsy243ftffjjy1cx9lm3o2bw%2Fpublic%2F1773274827%2FClaude+Certified+Architect+%E2%80%93+Foundations+Certification+Exam+Guide.pdf"
    type: exam_guide
    covers: "Scope authority; the three loop-termination anti-patterns"
---

# Task Statement 1.1: Design and implement agentic loops for autonomous task execution

## Overview

An **agentic loop** is the control flow that lets Claude work on a multi-step task autonomously: it decides what to do, takes an action, sees the result, and decides again — until the task is done. It's the single most foundational idea in Domain 1, and it underpins almost everything else on the exam: subagents, orchestration, workflows, and reliability all sit on top of a loop.

Anthropic exposes this loop at two levels, and it's worth knowing both:

- The **Agent SDK** runs the loop *for you*. You hand it a prompt and a set of tools, and it "evaluates your prompt, calls tools to take action, receives the results, and repeats until the task is complete" ([Agent SDK — agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)). You consume a stream of messages and read the outcome off a final `ResultMessage`.
- The **Messages API** is the layer underneath. Here there is no built-in loop — *you* write it: call the model, look at why it stopped, run any tools it asked for, feed the results back, and call again.

Task Statement 1.1 says "**design and implement**" — so this lesson builds the loop by hand on the Messages API. That's the version the exercise grades, and the version that teaches you what the SDK is doing under the hood. We'll map the hand-built loop back to the SDK's vocabulary as we go.

## How it works

The loop is short. Each pass does four things:

1. **Call the model** with the full conversation and the available tools.
2. **Inspect `response.stop_reason`** — the protocol-level field that tells you *why the model stopped generating this turn*.
3. **If `stop_reason == "tool_use"`**, the model is asking you to run one or more tools. Execute each requested tool, then append the results to the conversation as a `user` message made of `tool_result` blocks, and loop again.
4. **If `stop_reason == "end_turn"`**, the model is finished. Return the final message.

The key mechanic is that **tool results re-enter the conversation between iterations**. The model's *next* decision is informed by the *previous* tool's output — that's the whole point of the loop. You are the conduit that ferries tool calls outward and tool results back inward. The conversation history (and therefore the context window) grows every turn: "everything accumulates — the system prompt, tool definitions, conversation history, tool inputs, and tool outputs" ([Agent SDK — the context window](https://code.claude.com/docs/en/agent-sdk/agent-loop#the-context-window)).

A few details that matter:

- **`stop_reason` is a small enum, not free text.** On the Messages API the common values are `"tool_use"` (the model wants to call tools), `"end_turn"` (the model is done), and `"max_tokens"` (it hit the output limit mid-thought). You branch on these — you never read the model's prose to figure out what it wants.
- **Text and tool calls can coexist in one turn.** A single assistant response can contain a `text` block *and* one or more `tool_use` blocks. So "the response has text, therefore it's done" is simply false — the model often narrates ("Let me check the weather…") while requesting a tool in the same breath.
- **Multiple tools can be requested at once.** When `stop_reason == "tool_use"`, iterate *all* the content blocks, run every `tool_use` block, and return *all* their results in a single `user` message. The SDK does the same — when Claude requests several calls in one turn it can run them together ([Agent SDK — parallel tool execution](https://code.claude.com/docs/en/agent-sdk/agent-loop#parallel-tool-execution)).

Here's the mechanism in raw Messages-API code. Note what we dispatch on — `stop_reason`, and nothing else:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=tools,                 # list of tool-use schemas
    messages=messages,           # the conversation so far
)

# The model tells YOU why it stopped — you don't infer it.
if response.stop_reason == "tool_use":
    for block in response.content:
        if block.type == "tool_use":
            result = run_tool(block.name, block.input)  # your dispatch
            # ...wrap result in a tool_result block and append to messages
elif response.stop_reason == "end_turn":
    ...  # done
```

### Mapping to the SDK

When you use the Agent SDK instead, this same loop runs internally. You don't see `stop_reason == "tool_use"`; you see a stream of `AssistantMessage` and `UserMessage` events, and the loop "continues until Claude produces output with no tool calls" ([Agent SDK — turns and messages](https://code.claude.com/docs/en/agent-sdk/agent-loop#turns-and-messages)). The final `ResultMessage` carries a `stop_reason` too — `end_turn`, `max_tokens`, or `refusal` — which is the same protocol field surfacing at a higher level. The "safety cap" we'll add by hand below is the SDK's `max_turns` option, which "counts tool-use turns only."

## Worked example

Putting the four steps together gives a complete, reusable loop. This is the shape you'll implement in the exercise:

```python
def run_agent_loop(client, messages, tools, tool_handler, safety_cap=25):
    for _ in range(safety_cap):              # safety net, NOT the termination signal
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return response                  # the only real exit

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = tool_handler(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"unexpected stop_reason: {response.stop_reason}")

    raise RuntimeError("safety cap reached without end_turn")
```

Walking through it:

- **The assistant turn is appended before we process tools.** The Messages API requires the conversation to alternate correctly: the `tool_result` blocks you send next must follow the assistant turn that contained the matching `tool_use` blocks. Append the assistant `response.content` first, then the `user` tool-result message.
- **Each `tool_result` carries the `tool_use_id`** of the call it answers, so the model can line results up with requests. The `content` is whatever your handler returned for that tool.
- **`return` happens on `end_turn`.** That's the loop's real exit. Everything else is plumbing.
- **`safety_cap` is a guard, not the logic.** If the loop somehow never sees `end_turn` in 25 turns, we raise rather than spin forever — exactly what the SDK's `max_turns` does. But the *intended* way to leave the loop is the `end_turn` return.

## Anti-patterns & pitfalls

The exam guide calls out three specific anti-patterns for loop termination under Task Statement 1.1 (in its "Skills in: Avoiding anti-patterns such as…" list). Each one substitutes some other signal for `stop_reason` — and each one breaks:

1. **Parsing natural-language signals to decide termination.** Checking whether the assistant "said it's done" — `if "let me know" in text` or `if "i'm finished" in text`. Models phrase completion a hundred ways; string-matching misses most of them and false-fires on the rest. You'll terminate early on a polite mid-task aside and run forever when the phrasing doesn't match your list.
2. **Using an iteration cap as the primary stopping mechanism.** `for _ in range(10): ...` and calling it done. A cap is a fine *safety net* (that's exactly what `max_turns` / our `safety_cap` is), but it can't be your real signal. Real tasks need a variable number of turns; a hard cap turns "I'm not done yet" into "I guess we're done."
3. **Checking for assistant text content as a completion indicator.** "If the response has text and no tool calls, we're done." Wrong, because — as covered above — text and `tool_use` can appear in the *same* turn. Text presence is not the absence of more work.

All three share one root error: they treat the model's *output content* as the termination signal instead of the protocol field built for exactly this. **The Anthropic-prescribed approach is to dispatch on `stop_reason` and nothing else.** This is not "one option among several" — on this exam it is *the* correct answer, and the alternatives above are *wrong*, not merely weaker.

One more practical pitfall: **forgetting to append the assistant turn before the tool results.** If you send `tool_result` blocks without the preceding assistant message that requested them, the Messages API rejects the conversation. Append assistant content first, every time.

## Exam focus

This task statement is the backbone of every question about agent reliability, so it shows up across multiple CCA-F scenarios:

- **Scenario 1 (Customer Support Resolution Agent)** — the agent has to know when it has finished investigating before it responds to the customer.
- **Scenario 3 (Multi-Agent Research System)** — the coordinator's loop is what drives every subagent invocation; if the loop logic is wrong, the whole system is.
- **Scenario 4 (Developer Productivity with Claude)** — tools that orchestrate `Read`/`Write`/`Bash`/`Grep` are just agentic loops over the built-in toolset.

Expect distractors that "feel right": confidence thresholds, text-pattern checks, sentiment analysis, fixed iteration counts. The correct answer is always the one that uses the protocol-level signal (`stop_reason`) Anthropic designed for termination.

## References & further reading

- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — the loop lifecycle, turns, tool execution, `stop_reason`, and `max_turns`/budget caps. The single best reference for this lesson.
- [How Claude Code works — the agentic loop](https://code.claude.com/docs/en/how-claude-code-works) — the same loop, described conceptually (not SDK-specific).
- [Messages API — tool use](https://platform.claude.com/docs/en/build-with-claude/tool-use) — the raw `tool_use` / `tool_result` block shapes and the full set of `stop_reason` values you branch on when you build the loop by hand.
- **CCA-F Exam Guide, Domain 1, Task Statement 1.1** — the scope authority for what's testable here, including the three anti-patterns above (linked from the README).
