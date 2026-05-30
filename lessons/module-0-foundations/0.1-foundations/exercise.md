# Foundations: the four technologies — exercise

## What you're building

Implement `recommend_technology` in `recommender.py`. It's the decision tree from the lesson: given a task's signals, name the primary technology to reach for first — the Messages API, the Agent SDK, Claude Code, or MCP.

This is a **pure-logic** exercise. No Anthropic API calls, no network, no API key. You're encoding judgment about *which technology fits which task*, which is the whole point of an orientation chapter.

## Function signature

```python
def recommend_technology(task):
    """
    Args:
        task: dict of boolean signals. Recognized keys:
            connect_external_system — the need is to connect Claude to an
                                      outside system (DB, tracker, API).
            interactive_coding      — a developer is coding interactively in a
                                      terminal/IDE (or automating coding work).
            needs_autonomous_loop   — an autonomous multi-step agent must run
                                      inside your own application/process.
            Any missing key is treated as False.

    Returns:
        One of TECHNOLOGIES: "messages_api", "agent_sdk", "claude_code", or "mcp".
    """
```

## Requirements

You must:

1. **Check the signals in priority order** and return the matching technology:
   - `connect_external_system` → `"mcp"`
   - `interactive_coding` → `"claude_code"`
   - `needs_autonomous_loop` → `"agent_sdk"`
2. **Default to `"messages_api"`** when no special signal is set — the floor of the stack. A single model call is enough; one request, one response.
3. **Return only keys from `TECHNOLOGIES`.** Never invent a fifth value.
4. **Pass every test in `test_recommender.py`.**

You must NOT:

5. **Default the fallback to `"agent_sdk"` (or any non-`messages_api` value).** This is the chapter's central anti-pattern: reaching for the Agent SDK when the raw Messages API suffices. When a task has no loop, no tools, and no integration, the answer is the Messages API — not an agent framework. If your final `return` (the no-signal case) hands back `"agent_sdk"`, you've built the wrong thing.

Requirement 5 is graded directly by the rubric (`check: anti_pattern`). The verifier will read your code looking for it, and it fails the rubric whether or not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/0.1
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

There's nothing to mock — the exercise touches no API. The tests are plain assertions over the decision tree.

When you're ready (or stuck), run `/verify 0.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't. The decision tree and the four anti-patterns are right there.
- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) — the Client-SDK-vs-Agent-SDK comparison ("you implement a tool loop" vs. "Claude handles it") is exactly the `messages_api` vs. `agent_sdk` distinction you're encoding.
- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp) — what makes a task an MCP task (connecting to an external system).
