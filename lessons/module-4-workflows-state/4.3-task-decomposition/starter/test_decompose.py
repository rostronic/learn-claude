"""Tests for the task-decomposition planner. Pure logic — no SDK, no network."""

import pytest

from decompose import decompose, parallel_batches, validate_plan

FINDERS = {"style-checker", "security-scanner", "test-runner"}


def test_decompose_finders_are_parallel_with_no_deps():
    plan = decompose("review this PR")
    finders = [s for s in plan if s["name"] in FINDERS]
    assert len(finders) == 3
    for s in finders:
        assert s["parallel_group"] == 0
        assert s["depends_on"] == []


def test_decompose_synthesis_depends_on_all_finders_in_later_group():
    plan = decompose("review this PR")
    synthesis = next(s for s in plan if s["name"] == "synthesis")
    assert synthesis["parallel_group"] == 1
    assert set(synthesis["depends_on"]) == FINDERS


def test_no_subtask_can_spawn_subagents():
    plan = decompose("review this PR")
    for s in plan:
        assert "Agent" not in s["tools"]


def test_read_only_finders_have_least_privilege_tools():
    plan = decompose("review this PR")
    for name in ("style-checker", "security-scanner"):
        s = next(p for p in plan if p["name"] == name)
        assert s["tools"] == ["Read", "Grep", "Glob"]
    test_runner = next(p for p in plan if p["name"] == "test-runner")
    assert "Bash" in test_runner["tools"]  # needs to execute tests


def test_validate_plan_accepts_the_good_plan():
    assert validate_plan(decompose("review this PR")) == []


def test_validate_plan_flags_agent_in_tools():
    bad = [{"name": "a", "tools": ["Read", "Agent"], "depends_on": [], "parallel_group": 0}]
    problems = validate_plan(bad)
    assert any("Agent" in p for p in problems)


def test_validate_plan_flags_dependency_inversion():
    # "early" runs in group 0 but depends on "late" in group 1 — impossible ordering.
    bad = [
        {"name": "early", "tools": ["Read"], "depends_on": ["late"], "parallel_group": 0},
        {"name": "late", "tools": ["Read"], "depends_on": [], "parallel_group": 1},
    ]
    assert validate_plan(bad) != []


def test_validate_plan_flags_unknown_dependency():
    bad = [{"name": "a", "tools": ["Read"], "depends_on": ["ghost"], "parallel_group": 1}]
    assert any("ghost" in p for p in validate_plan(bad))


def test_parallel_batches_orders_groups():
    batches = parallel_batches(decompose("review this PR"))
    assert set(batches[0]) == FINDERS
    assert batches[1] == ["synthesis"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
