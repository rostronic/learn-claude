"""Tests for build_subagent_invocation. Pure logic — no API key, no model calls."""

import pytest

from subagent_config import build_subagent_invocation
from registry import AGENT_REGISTRY

FINDINGS = [
    {"source": "https://a.example/rest", "title": "REST guide", "content": "REST is stateless."},
    {"source": "https://b.example/grpc", "title": "gRPC guide", "content": "gRPC uses HTTP/2."},
]


def test_raises_without_spawn_permission():
    """No 'Task'/'Agent' in allowed_tools -> the coordinator cannot spawn subagents."""
    with pytest.raises(PermissionError):
        build_subagent_invocation(
            "researcher", AGENT_REGISTRY, ["Read", "Grep"], "research REST", FINDINGS
        )


def test_accepts_both_task_and_agent_tool_names():
    """The exam says 'Task'; current SDKs emit 'Agent'. Either must enable spawning."""
    for tool in ("Task", "Agent"):
        result = build_subagent_invocation(
            "researcher", AGENT_REGISTRY, ["Read", tool], "research REST", FINDINGS
        )
        assert result["name"] == "researcher"


def test_unknown_agent_raises_keyerror():
    with pytest.raises(KeyError):
        build_subagent_invocation(
            "nonexistent", AGENT_REGISTRY, ["Agent"], "do a thing", FINDINGS
        )


def test_prior_findings_embedded_with_attribution():
    """Every finding's content AND its source/title must reach the subagent prompt."""
    result = build_subagent_invocation(
        "synthesizer", AGENT_REGISTRY, ["Agent"], "compare REST vs gRPC", FINDINGS
    )
    prompt = result["prompt"]
    assert "compare REST vs gRPC" in prompt              # the task itself
    for f in FINDINGS:
        assert f["content"] in prompt                    # content passed explicitly
        assert f["source"] in prompt                     # attribution preserved
        assert f["title"] in prompt


def test_carries_system_prompt_and_tool_restrictions():
    """The result reflects the AgentDefinition's own system prompt and tools."""
    researcher = build_subagent_invocation(
        "researcher", AGENT_REGISTRY, ["Agent"], "research REST", FINDINGS
    )
    assert researcher["system"] == AGENT_REGISTRY["researcher"]["prompt"]
    assert researcher["tools"] == ["Read", "Grep", "Glob", "WebSearch"]

    # The synthesizer omits "tools" -> inherits all tools -> None in the spec.
    synthesizer = build_subagent_invocation(
        "synthesizer", AGENT_REGISTRY, ["Agent"], "synthesize", FINDINGS
    )
    assert synthesizer["tools"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
