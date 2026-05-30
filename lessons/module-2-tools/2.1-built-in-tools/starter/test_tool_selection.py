"""Tests for the tool-selection layer. Pure logic — no API key needed."""

import pytest

from tool_selection import plan_is_safe, requires_permission, select_tool


@pytest.mark.parametrize(
    "intent,expected",
    [
        ("read_file", "Read"),
        ("find_files_by_name", "Glob"),
        ("search_file_contents", "Grep"),
        ("edit_region_of_existing_file", "Edit"),
        ("create_or_overwrite_file", "Write"),
        ("run_command", "Bash"),
    ],
)
def test_select_tool_maps_each_intent(intent, expected):
    assert select_tool(intent) == expected


@pytest.mark.parametrize("intent", ["read_file", "find_files_by_name", "search_file_contents"])
def test_dedicated_ops_never_route_to_bash(intent):
    """The anti-pattern: don't shell out for jobs a dedicated tool covers."""
    assert select_tool(intent) != "Bash"


def test_select_tool_unknown_intent_raises():
    with pytest.raises(ValueError):
        select_tool("teleport_file")


@pytest.mark.parametrize("tool", ["Read", "Grep", "Glob"])
def test_read_only_tools_need_no_permission(tool):
    assert requires_permission(tool) is False


@pytest.mark.parametrize("tool", ["Bash", "Edit", "Write"])
def test_mutating_tools_require_permission(tool):
    assert requires_permission(tool) is True


def test_requires_permission_unknown_tool_raises():
    with pytest.raises(ValueError):
        requires_permission("Telekinesis")


def test_plan_safe_when_edit_follows_read():
    plan = [
        {"tool": "Read", "path": "a.py"},
        {"tool": "Edit", "path": "a.py"},
    ]
    assert plan_is_safe(plan) is True


def test_plan_unsafe_when_edit_has_no_prior_read():
    plan = [
        {"tool": "Edit", "path": "a.py"},
    ]
    assert plan_is_safe(plan) is False


def test_plan_unsafe_when_write_targets_unread_path():
    plan = [
        {"tool": "Read", "path": "a.py"},
        {"tool": "Write", "path": "b.py"},  # b.py was never read
    ]
    assert plan_is_safe(plan) is False


def test_plan_safe_with_multiple_files_each_read_first():
    plan = [
        {"tool": "Read", "path": "a.py"},
        {"tool": "Read", "path": "b.py"},
        {"tool": "Edit", "path": "b.py"},
        {"tool": "Write", "path": "a.py"},
        {"tool": "Bash", "path": "."},  # Bash is unaffected by the rule
    ]
    assert plan_is_safe(plan) is True


def test_plan_read_must_precede_not_follow():
    plan = [
        {"tool": "Edit", "path": "a.py"},
        {"tool": "Read", "path": "a.py"},  # too late
    ]
    assert plan_is_safe(plan) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
