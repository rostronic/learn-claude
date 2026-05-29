"""Starter skeleton for Learn Claude chapter 3.1 — Agentic Loops.

Implement run_agent_loop below. See exercise.md for the full spec.
"""

import os

import anthropic


def run_agent_loop(client, messages, tools, tool_handler):
    """Run an agentic loop until Claude signals end_turn.

    Args:
        client:        an anthropic.Anthropic() instance.
        messages:      list[dict] — conversation so far. Mutated in place
                       (assistant turns and tool_result messages are appended).
        tools:         list[dict] — Claude tool-use schemas
                       (use WEATHER_TOOL and TIME_TOOL from tools.py).
        tool_handler:  callable(name: str, input: dict) -> Any — invoked when
                       Claude requests a tool call. Returns the value that will
                       be wrapped in a tool_result block.

    Returns:
        The final assistant Message (the one whose stop_reason == "end_turn").
    """
    # TODO: implement
    #   1. Loop. Inside the loop:
    #        a. Call client.messages.create(model=..., max_tokens=..., tools=tools, messages=messages)
    #        b. Append the response as an assistant message to `messages`.
    #        c. If response.stop_reason == "end_turn": return response.
    #        d. If response.stop_reason == "tool_use": for each tool_use block in
    #           response.content, call tool_handler(block.name, block.input), and
    #           append a single user message containing all the tool_result blocks.
    #   2. Use a safety cap of ~25 iterations to guard against runaway loops, BUT
    #      do not use it as your termination signal. The real exit is end_turn.
    #   3. Do NOT inspect response text content to decide when to stop. The only
    #      termination signal is response.stop_reason.
    raise NotImplementedError("Implement run_agent_loop — see exercise.md")


if __name__ == "__main__":
    # Optional: try your loop against the real API after the tests pass.
    # Requires ANTHROPIC_API_KEY in the environment.
    from tools import TIME_TOOL, WEATHER_TOOL, get_time, get_weather

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY to run against the real API.")

    def handler(name, tool_input):
        if name == "get_weather":
            return get_weather(**tool_input)
        if name == "get_time":
            return get_time(**tool_input)
        raise ValueError(f"unknown tool: {name}")

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": "What's the weather in Paris and what time is it in Tokyo?"}]
    final = run_agent_loop(client, messages, [WEATHER_TOOL, TIME_TOOL], handler)
    print(final)
