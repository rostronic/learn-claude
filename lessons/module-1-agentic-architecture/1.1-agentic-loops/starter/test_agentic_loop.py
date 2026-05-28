"""Tests for run_agent_loop. These mock the Anthropic client — no API key needed."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agentic_loop import run_agent_loop
from tools import TIME_TOOL, WEATHER_TOOL, get_time, get_weather


def _tool_use_block(tool_id, name, tool_input):
    """Build a fake tool_use content block matching the Anthropic SDK shape."""
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)


def _text_block(text):
    return SimpleNamespace(type="text", text=text)


def _response(stop_reason, content):
    """Build a fake Message matching the bits of the SDK shape we care about."""
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def _handler(name, tool_input):
    if name == "get_weather":
        return get_weather(**tool_input)
    if name == "get_time":
        return get_time(**tool_input)
    raise ValueError(f"unknown tool: {name}")


def _mock_client(responses):
    """A fake anthropic.Anthropic() whose messages.create yields each response in turn."""
    client = MagicMock()
    client.messages.create.side_effect = list(responses)
    return client


def test_loop_runs_at_least_once_and_terminates_on_end_turn():
    """A trivial conversation with no tool calls — one round, end_turn, done."""
    client = _mock_client([
        _response("end_turn", [_text_block("Hi there!")]),
    ])
    messages = [{"role": "user", "content": "hello"}]
    final = run_agent_loop(client, messages, [WEATHER_TOOL, TIME_TOOL], _handler)

    assert client.messages.create.call_count == 1
    assert final.stop_reason == "end_turn"


def test_tool_call_results_are_appended_between_iterations():
    """Tool turn → tool_results appended as user message → next turn ends."""
    client = _mock_client([
        _response("tool_use", [_tool_use_block("toolu_1", "get_weather", {"location": "Paris"})]),
        _response("end_turn", [_text_block("It's 68°F and partly cloudy in Paris.")]),
    ])
    messages = [{"role": "user", "content": "weather in Paris?"}]
    final = run_agent_loop(client, messages, [WEATHER_TOOL, TIME_TOOL], _handler)

    # Two API calls: one that requested the tool, one that wrapped up.
    assert client.messages.create.call_count == 2
    assert final.stop_reason == "end_turn"

    # The assistant tool_use turn AND a user tool_result turn must both be in messages.
    roles = [m["role"] for m in messages]
    assert roles.count("assistant") >= 1
    assert roles.count("user") >= 2  # the original user message + the tool_result message

    # The tool_result message must reference the tool_use id and contain the handler's output.
    tool_result_msg = next(
        m for m in messages
        if m["role"] == "user"
        and isinstance(m.get("content"), list)
        and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])
    )
    block = tool_result_msg["content"][0]
    assert block["tool_use_id"] == "toolu_1"
    assert block["content"]["location"] == "Paris"


def test_multiple_tool_uses_in_one_turn_are_all_handled():
    """If Claude requests two tools in one turn, both results must be appended together."""
    client = _mock_client([
        _response("tool_use", [
            _tool_use_block("toolu_a", "get_weather", {"location": "Paris"}),
            _tool_use_block("toolu_b", "get_time", {"timezone": "Asia/Tokyo"}),
        ]),
        _response("end_turn", [_text_block("Done.")]),
    ])
    messages = [{"role": "user", "content": "weather in Paris and time in Tokyo?"}]
    run_agent_loop(client, messages, [WEATHER_TOOL, TIME_TOOL], _handler)

    tool_result_msg = next(
        m for m in messages
        if m["role"] == "user"
        and isinstance(m.get("content"), list)
        and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])
    )
    ids = {b["tool_use_id"] for b in tool_result_msg["content"]}
    assert ids == {"toolu_a", "toolu_b"}


def test_returns_final_message_object():
    """The return value is the end_turn Message, not None or a string."""
    final_resp = _response("end_turn", [_text_block("All done.")])
    client = _mock_client([
        _response("tool_use", [_tool_use_block("toolu_x", "get_weather", {"location": "Tokyo"})]),
        final_resp,
    ])
    messages = [{"role": "user", "content": "weather?"}]
    result = run_agent_loop(client, messages, [WEATHER_TOOL, TIME_TOOL], _handler)

    assert result is final_resp
    assert result.stop_reason == "end_turn"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
