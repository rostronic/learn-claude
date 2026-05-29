# Agentic loops — exercise

## What you're building

Implement `run_agent_loop` in `agentic_loop.py`. It's the control flow from the lesson: send a request, dispatch on `stop_reason`, execute tools, loop until `end_turn`.

## Function signature

```python
def run_agent_loop(client, messages, tools, tool_handler):
    """
    Run an agentic loop until Claude signals end_turn.

    Args:
        client:        an anthropic.Anthropic() instance
        messages:      list[dict] — conversation so far. Mutated in place
                       (tool calls and results are appended).
        tools:         list[dict] — Claude tool-use schemas
                       (use WEATHER_TOOL and TIME_TOOL from tools.py).
        tool_handler:  callable(name: str, input: dict) -> Any
                       — invoked when Claude requests a tool call. Returns
                       the result that will be wrapped in a tool_result block.

    Returns:
        The final assistant Message object (the one with stop_reason="end_turn").
    """
```

## Requirements

You must:

1. **Loop until `response.stop_reason == "end_turn"`.** Return the final response object.
2. **When `stop_reason == "tool_use"`,** iterate `response.content`, call `tool_handler(block.name, block.input)` for every `tool_use` block, and append a single `user` message containing `tool_result` blocks for all of them.
3. **Append the assistant response to `messages`** before processing tool calls — Claude needs to see its own prior turn on the next iteration.
4. **Use the two tools in `tools.py`** (`WEATHER_TOOL` and `TIME_TOOL`).
5. **Pass every test in `test_agentic_loop.py`.**

You must NOT:

6. **Use the iteration counter as your primary termination signal.** A safety cap of 25 iterations is allowed and encouraged — runaway loops are real and you should guard against them — but the loop must *exit* on `end_turn`, not on hitting the cap. If your code says "well, we did 10 iterations, must be done," you've built the wrong thing.
7. **Inspect assistant text content to decide when to stop.** No `if "done" in response.content[0].text:`. No checks for the absence of tool calls. The only termination signal is `response.stop_reason`.

These two anti-patterns are graded directly by the rubric (`check: anti_pattern`). The verifier will read your code looking for them. They will fail the rubric whether or not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/3.1
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests mock the Anthropic client — you do not need an `ANTHROPIC_API_KEY` to run them, and you will not burn API credits. If you want to also run your loop against the real API after the tests pass, set `ANTHROPIC_API_KEY` and write a short `if __name__ == "__main__":` block at the bottom of `agentic_loop.py`.

When you're ready (or stuck), run `/verify 3.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — the loop lifecycle, `stop_reason`, and `max_turns` (the SDK's version of your `safety_cap`).
- [Messages API — tool use](https://platform.claude.com/docs/en/build-with-claude/tool-use) — the exact `tool_use` / `tool_result` block shapes you'll construct.
