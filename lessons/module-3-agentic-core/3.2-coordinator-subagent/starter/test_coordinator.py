"""Tests for run_coordinator. These mock the Anthropic client and use a spy
subagent spawner — no API key needed, no API credits burned."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from coordinator import run_coordinator
from subagents import RESEARCHER, SYNTHESIZER


def _tool_use_block(tool_id, name, task):
    """Fake tool_use content block: the coordinator invoking a subagent."""
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input={"task": task})


def _text_block(text):
    return SimpleNamespace(type="text", text=text)


def _response(stop_reason, content):
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def _mock_client(responses):
    """A fake anthropic.Anthropic() whose messages.create yields each response in turn."""
    client = MagicMock()
    client.messages.create.side_effect = list(responses)
    return client


def _spy_spawner():
    """A spy spawn_subagent(name, task) -> str that records every call."""
    calls = []

    def spawn(name, task):
        calls.append((name, task))
        return f"[{name} result for: {task}]"

    return spawn, calls


TOOLS = [RESEARCHER, SYNTHESIZER]


def test_trivial_query_answers_directly_without_subagents():
    """A simple query the coordinator can answer itself: one turn, end_turn, no spawns."""
    client = _mock_client([
        _response("end_turn", [_text_block("REST and gRPC differ in...")]),
    ])
    spawn, calls = _spy_spawner()
    final = run_coordinator(client, "What is REST?", TOOLS, spawn)

    assert client.messages.create.call_count == 1
    assert final.stop_reason == "end_turn"
    assert calls == []  # dynamic selection: no subagents needed for a trivial query


def test_single_subagent_dispatch_with_isolated_context():
    """Coordinator invokes one subagent, then synthesizes. The subagent receives ONLY
    the composed task string — not the coordinator's history."""
    client = _mock_client([
        _response("tool_use", [_tool_use_block("toolu_1", "researcher", "tradeoffs of gRPC")]),
        _response("end_turn", [_text_block("Here is the comparison...")]),
    ])
    spawn, calls = _spy_spawner()
    final = run_coordinator(client, "Compare REST vs gRPC", TOOLS, spawn)

    assert client.messages.create.call_count == 2
    assert final.stop_reason == "end_turn"

    # Exactly one subagent spawned, with the name and task the model asked for —
    # and the second arg is the task STRING, proving context isolation (not history).
    assert calls == [("researcher", "tradeoffs of gRPC")]

    # The subagent's result is routed back into the coordinator's conversation.
    messages = client.messages.create.call_args.kwargs["messages"]
    tool_result_msg = next(
        m for m in messages
        if m["role"] == "user"
        and isinstance(m.get("content"), list)
        and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])
    )
    block = tool_result_msg["content"][0]
    assert block["tool_use_id"] == "toolu_1"
    assert block["content"] == "[researcher result for: tradeoffs of gRPC]"


def test_multiple_subagents_in_one_turn_all_dispatched():
    """A fan-out turn: the coordinator requests two subagents at once. Both run, and
    both results are bundled into a single tool_result user message."""
    client = _mock_client([
        _response("tool_use", [
            _tool_use_block("toolu_a", "researcher", "REST tradeoffs"),
            _tool_use_block("toolu_b", "researcher", "gRPC tradeoffs"),
        ]),
        _response("end_turn", [_text_block("Done.")]),
    ])
    spawn, calls = _spy_spawner()
    run_coordinator(client, "Compare REST vs gRPC", TOOLS, spawn)

    assert calls == [("researcher", "REST tradeoffs"), ("researcher", "gRPC tradeoffs")]

    messages = client.messages.create.call_args.kwargs["messages"]
    tool_result_msg = next(
        m for m in messages
        if m["role"] == "user"
        and isinstance(m.get("content"), list)
        and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])
    )
    ids = {b["tool_use_id"] for b in tool_result_msg["content"]}
    assert ids == {"toolu_a", "toolu_b"}


def test_returns_final_message_object():
    """The return value is the end_turn Message object itself."""
    final_resp = _response("end_turn", [_text_block("All done.")])
    client = _mock_client([
        _response("tool_use", [_tool_use_block("toolu_x", "synthesizer", "merge these")]),
        final_resp,
    ])
    spawn, _ = _spy_spawner()
    result = run_coordinator(client, "synthesize", TOOLS, spawn)

    assert result is final_resp
    assert result.stop_reason == "end_turn"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
