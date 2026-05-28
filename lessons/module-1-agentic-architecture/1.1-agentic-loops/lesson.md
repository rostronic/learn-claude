# Task Statement 1.1: Design and implement agentic loops for autonomous task execution

## Concept

An agentic loop is the control flow that lets Claude execute multi-step tasks autonomously. The shape is always the same:

1. Send the conversation to Claude via `client.messages.create(...)`.
2. Inspect `response.stop_reason`.
3. If `"tool_use"` — execute every requested tool, append the results to the message history as a `user` message containing `tool_result` blocks, and loop back to step 1.
4. If `"end_turn"` — Claude is done. Return the final assistant message.

Tool results get appended to `messages` *between iterations* so Claude can reason about new information on the next turn. That's the whole point of the loop: the model's next decision is informed by the prior tool's output. You are the conduit that ferries tool calls outward and tool results inward.

There's a deeper distinction the exam tests on: this is **model-driven decision-making**. Claude decides which tool to call next based on the conversation state. You don't decide. You don't write a switch statement. You don't pre-configure a tool sequence. If you find yourself writing `if user_asked_about_weather: call_weather_tool()`, you've built a decision tree dressed up as an agent, and the exam will catch you on it.

## Anti-pattern

The CCA-F exam guide lists three specific anti-patterns for loop termination (Domain 1, Task Statement 1.1, "Skills in: Avoiding anti-patterns such as…"):

1. **Parsing natural-language signals to determine loop termination** — e.g. checking if the assistant said "I'm done" or "Let me know if you need anything else." This is a string-matching trap. Models phrase completion a hundred different ways. You will miss most of them and falsely terminate on the rest.
2. **Setting arbitrary iteration caps as the primary stopping mechanism** — `for _ in range(10): ...` and calling it a day. The cap is fine as a *safety net* against runaway loops, but it can't be your real termination signal. Real tasks need variable iteration counts; a cap turns "I'm not done yet" into "I'm done, I guess."
3. **Checking for assistant text content as a completion indicator** — "if the response has text and no tool calls, we're done." Wrong. The model can emit text *alongside* tool calls in the same turn. Text presence is not absence of more work.

All three share a root cause: they treat the output content as the termination signal instead of the protocol-level field Anthropic designed for exactly this purpose.

## Correct pattern

**Check `stop_reason`. Nothing else.** This is the Anthropic-prescribed approach and the exam treats it as the only correct answer.

```python
def run_agent_loop(client, messages, tools, tool_handler, safety_cap=25):
    for _ in range(safety_cap):              # safety net, NOT termination signal
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
```

Three things to notice:

- The `for _ in range(safety_cap)` is a guard against runaway loops, not the termination logic. Termination is the `return` on `end_turn`.
- Tool results are appended as a `user` message with `tool_result` blocks. Claude's next call will see them and reason about them.
- We never look at `response.content` text to decide what to do. We dispatch on `stop_reason` only.

## Why this matters on the exam

This is the foundation of every scenario question about agent reliability. If you can't articulate the loop in terms of `stop_reason`, you'll miss questions across **Scenario 1** (customer support agent that has to know when it's finished investigating), **Scenario 3** (multi-agent research where the coordinator's loop drives every subagent invocation), and **Scenario 4** (developer productivity tools that orchestrate Read/Write/Bash/Grep). The exam reliably offers distractors that "feel right" — confidence thresholds, text-pattern checks, sentiment analysis — and the correct answer is always the one that uses the protocol-level signal Anthropic designed.
