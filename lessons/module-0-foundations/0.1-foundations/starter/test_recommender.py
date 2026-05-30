"""Tests for recommend_technology. Pure logic — no API key, no network."""

import pytest

from recommender import EXPLANATIONS, TECHNOLOGIES, recommend_technology


def test_external_system_need_routes_to_mcp():
    """Connecting Claude to an outside system is an MCP job."""
    task = {"connect_external_system": True}
    assert recommend_technology(task) == "mcp"


def test_interactive_coding_routes_to_claude_code():
    """A developer coding interactively reaches for Claude Code."""
    task = {"interactive_coding": True}
    assert recommend_technology(task) == "claude_code"


def test_autonomous_loop_routes_to_agent_sdk():
    """An embedded multi-step agent in your own process is the Agent SDK."""
    task = {"needs_autonomous_loop": True}
    assert recommend_technology(task) == "agent_sdk"


def test_simple_task_falls_back_to_messages_api():
    """No special signal -> a single Messages API call is enough.

    This is the anti-pattern guard: the floor is the raw Messages API, NOT
    the heavier Agent SDK. A plain prompt->response task must not be told to
    reach for an agent framework.
    """
    assert recommend_technology({}) == "messages_api"
    assert recommend_technology({"needs_autonomous_loop": False}) == "messages_api"


def test_connection_need_takes_priority_over_a_loop():
    """When several signals are set, the more specific need wins (priority order)."""
    task = {"connect_external_system": True, "needs_autonomous_loop": True}
    assert recommend_technology(task) == "mcp"


def test_always_returns_a_known_technology():
    """Every recommendation is one of the four known technology keys."""
    sample_tasks = [
        {},
        {"connect_external_system": True},
        {"interactive_coding": True},
        {"needs_autonomous_loop": True},
        {"unknown_signal": True},
    ]
    for task in sample_tasks:
        assert recommend_technology(task) in TECHNOLOGIES


def test_every_technology_has_an_explanation():
    """The orientation table must describe all four technologies."""
    assert set(EXPLANATIONS) == set(TECHNOLOGIES)
    assert all(EXPLANATIONS[tech].strip() for tech in TECHNOLOGIES)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
