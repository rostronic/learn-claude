"""Tests for the tool-distribution helpers. Pure logic — no API key, no model calls."""

import pytest

from tool_distribution import build_agent_toolset, tool_choice_any, tool_choice_force

SCOPES = {
    "researcher": ["Read", "Grep", "Glob", "WebSearch"],
    "synthesizer": ["Read", "verify_fact"],
}


def test_unknown_role_raises_keyerror():
    with pytest.raises(KeyError):
        build_agent_toolset("nope", SCOPES)


def test_over_provisioned_role_raises():
    over = {"kitchen_sink": ["t1", "t2", "t3", "t4", "t5", "t6"]}  # 6 > default max 5
    with pytest.raises(ValueError):
        build_agent_toolset("kitchen_sink", over)


def test_returns_scoped_copy():
    tools = build_agent_toolset("synthesizer", SCOPES)
    assert tools == ["Read", "verify_fact"]
    # It must be a copy — mutating the result must not corrupt the registry.
    tools.append("WebSearch")
    assert SCOPES["synthesizer"] == ["Read", "verify_fact"]


def test_tool_choice_constructors():
    assert tool_choice_any() == {"type": "any"}
    assert tool_choice_force("extract_metadata") == {"type": "tool", "name": "extract_metadata"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
