"""Starter skeleton for Learn Claude Lesson 1.3 — Subagent invocation & context passing.

Implement build_subagent_invocation below. See exercise.md for the full spec.
"""

import json  # noqa: F401  (useful for embedding structured findings)

from registry import SPAWN_TOOLS  # noqa: F401  ({"Task", "Agent"} — accepted spawn tools)


def build_subagent_invocation(agent_name, registry, allowed_tools, task, prior_findings):
    """Assemble one subagent invocation spec.

    Args:
        agent_name:     str — which subagent type to spawn (a key in `registry`).
        registry:       dict[str, dict] — AgentDefinitions keyed by name. Each value has
                        "description", "prompt" (system prompt), and optional "tools".
        allowed_tools:  list[str] — the coordinator's allowed tools. Spawning requires
                        "Task" or "Agent" to be present.
        task:           str — what this subagent should accomplish.
        prior_findings: list[dict] — findings from earlier agents to pass in explicitly,
                        e.g. {"source": ..., "title": ..., "content": ...}.

    Returns:
        dict with keys "name", "system", "prompt", "tools" (see exercise.md).

    Raises:
        PermissionError if neither "Task" nor "Agent" is in allowed_tools.
        KeyError        if agent_name is not in registry.
    """
    # TODO: implement
    #   1. If neither "Task" nor "Agent" is in allowed_tools, raise PermissionError.
    #   2. If agent_name not in registry, raise KeyError. Otherwise look up its definition.
    #   3. Compose a "prompt" that embeds the task AND every prior_findings entry,
    #      preserving each finding's source/attribution metadata (don't flatten to bare
    #      content). The subagent inherits nothing — this prompt is its only context.
    #   4. Return {"name", "system": <agent's prompt>, "prompt": <composed>, "tools": <agent's tools or None>}.
    raise NotImplementedError("Implement build_subagent_invocation — see exercise.md")
