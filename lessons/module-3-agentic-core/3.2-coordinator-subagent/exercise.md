# Coordinator and subagent orchestration — exercise

## What you're building

Implement `run_coordinator` in `coordinator.py`. It's a hub-and-spoke orchestrator: a coordinator agentic loop whose "tools" are subagents. The coordinator decides which subagents to invoke, hands each one an explicit task, and aggregates the results — routing everything through itself.

This builds on chapter 3.1: the coordinator is the same `stop_reason` loop, except each tool call spawns a subagent in **isolated context**.

## Function signature

```python
def run_coordinator(client, query, subagent_tools, spawn_subagent, safety_cap=25):
    """
    Run a coordinator agentic loop. The coordinator's tools ARE subagents.

    Args:
        client:         an anthropic.Anthropic() instance.
        query:          str — the user's request. Seed the conversation with it.
        subagent_tools: list[dict] — Claude tool-use schemas, one per subagent type
                        (use RESEARCHER and SYNTHESIZER from subagents.py). Each has a
                        required "task" input the coordinator fills in per invocation.
        spawn_subagent: callable(name: str, task: str) -> str — spawns the named subagent
                        in ISOLATED context. It receives ONLY `task` and returns its final
                        text. You must NOT pass it the coordinator's message history.
        safety_cap:     int — runaway-loop guard, NOT the termination signal.

    Returns:
        The final coordinator Message object (stop_reason == "end_turn").
    """
```

## Requirements

You must:

1. **Seed the conversation** with the `query` as the first user message.
2. **Loop on `stop_reason`** (as in 1.1): continue on `"tool_use"`, return the final response on `"end_turn"`.
3. **For each `tool_use` block,** call `spawn_subagent(block.name, block.input["task"])` and append a single `user` message containing a `tool_result` block per subagent invocation (with the matching `tool_use_id`).
4. **Append the assistant response to the conversation** before processing tool calls.
5. **Pass every test in `test_coordinator.py`.**

You must NOT:

6. **Pass the coordinator's conversation history (or any parent state) into `spawn_subagent`.** A subagent's only context is the `task` string you hand it — that's the whole point of context isolation. Passing `messages`, the full transcript, or another subagent's raw output as the "task" is the wrong pattern.
7. **Hardcode a fixed subagent pipeline.** Don't call the subagents in a predetermined sequence regardless of what the coordinator (the model) requests. Which subagents run, and in what order, is decided per query by the `tool_use` blocks the model emits — not by an `if`/`for` pipeline you write.

Requirement 6 is graded directly by the rubric (`check: anti_pattern`). The verifier will read your code looking for the coordinator's history leaking into a subagent.

## How to run it

```bash
cd ~/learn-claude-work/3.2
pip install -r requirements.txt
pytest -v
```

The tests mock the Anthropic client and use a spy `spawn_subagent` — no `ANTHROPIC_API_KEY` needed, no API credits burned.

When you're ready (or stuck), run `/verify 3.2` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first.
- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — context isolation and what subagents inherit.
- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — the loop the coordinator runs.
