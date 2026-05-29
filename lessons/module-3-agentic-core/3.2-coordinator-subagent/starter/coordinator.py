"""Starter skeleton for Learn Claude chapter 3.2 — Coordinator-Subagent Orchestration.

Implement run_coordinator below. See exercise.md for the full spec.
"""

import os

import anthropic


def run_coordinator(client, query, subagent_tools, spawn_subagent, safety_cap=25):
    """Run a coordinator agentic loop whose 'tools' are subagents.

    Args:
        client:         an anthropic.Anthropic() instance.
        query:          str — the user's request. Seed the conversation with it.
        subagent_tools: list[dict] — Claude tool-use schemas, one per subagent type
                        (use RESEARCHER and SYNTHESIZER from subagents.py).
        spawn_subagent: callable(name: str, task: str) -> str — spawns the named
                        subagent in ISOLATED context. It receives ONLY `task` and
                        returns its final text. Do NOT pass it the coordinator's
                        message history.
        safety_cap:     int — runaway-loop guard, NOT the termination signal.

    Returns:
        The final coordinator Message (stop_reason == "end_turn").
    """
    # TODO: implement
    #   1. Seed messages = [{"role": "user", "content": query}].
    #   2. Loop (up to safety_cap). Inside the loop:
    #        a. response = client.messages.create(model=..., max_tokens=...,
    #                                              tools=subagent_tools, messages=messages)
    #        b. Append the response as an assistant message to `messages`.
    #        c. If response.stop_reason == "end_turn": return response.
    #        d. If response.stop_reason == "tool_use": for each tool_use block, call
    #           spawn_subagent(block.name, block.input["task"]) and collect a
    #           tool_result block (type/tool_use_id/content) for each. Append them as a
    #           single user message.
    #   3. The subagent gets ONLY the task string — never `messages` or parent state.
    raise NotImplementedError("Implement run_coordinator — see exercise.md")


if __name__ == "__main__":
    # Optional: run against the real API after the tests pass. Requires ANTHROPIC_API_KEY.
    from subagents import RESEARCHER, SYNTHESIZER, spawn_subagent

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY to run against the real API.")

    client = anthropic.Anthropic()
    final = run_coordinator(
        client,
        "Compare the tradeoffs of REST vs gRPC for internal microservices.",
        [RESEARCHER, SYNTHESIZER],
        spawn_subagent,
    )
    print(final)
