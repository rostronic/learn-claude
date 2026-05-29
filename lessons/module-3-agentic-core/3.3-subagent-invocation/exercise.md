# Subagent invocation and context passing — exercise

## What you're building

Implement `build_subagent_invocation` in `subagent_config.py`. It assembles a single, correctly-configured subagent invocation: it enforces the spawning permission, looks up the subagent's `AgentDefinition`, and composes a prompt that carries **explicit, attributed** context — because subagents inherit nothing.

This is pure logic — no API calls, no model. You're building the invocation *spec* the coordinator would hand to the Task/Agent tool.

## Function signature

```python
def build_subagent_invocation(agent_name, registry, allowed_tools, task, prior_findings):
    """
    Assemble one subagent invocation spec.

    Args:
        agent_name:     str — which subagent type to spawn (a key in `registry`).
        registry:       dict[str, dict] — AgentDefinitions keyed by name. Each value has
                        "description", "prompt" (the subagent's system prompt), and an
                        optional "tools" (list of allowed tool names).
        allowed_tools:  list[str] — the coordinator's allowed tools. Spawning requires
                        "Task" or "Agent" to be present.
        task:           str — what this subagent should accomplish.
        prior_findings: list[dict] — findings from earlier agents to pass in explicitly,
                        each like {"source": ..., "title": ..., "content": ...}.

    Returns:
        dict with keys:
          "name":   the agent_name
          "system": the subagent's own system prompt (registry[agent_name]["prompt"])
          "prompt": the composed task prompt, with prior_findings embedded (attribution preserved)
          "tools":  registry[agent_name].get("tools")  (None => inherits all tools)

    Raises:
        PermissionError if neither "Task" nor "Agent" is in allowed_tools.
        KeyError        if agent_name is not in registry.
    """
```

## Requirements

You must:

1. **Gate on the spawning permission.** If neither `"Task"` nor `"Agent"` is in `allowed_tools`, raise `PermissionError`. (The exam guide says "Task"; current SDKs emit "Agent" — accept either.)
2. **Look up the AgentDefinition** for `agent_name` in `registry`; raise `KeyError` if it's missing.
3. **Pass context explicitly.** Embed every entry of `prior_findings` into the composed `"prompt"` so the subagent actually receives it — including each finding's source/attribution metadata, not just its content.
4. **Carry the subagent's own config** into the result: its system `prompt` and its `tools` restriction (`None` if the definition omits `tools`).
5. **Pass every test in `test_subagent_config.py`.**

You must NOT:

6. **Assume implicit context inheritance.** Do not rely on the subagent "remembering" anything or sharing memory across invocations. Everything it needs must be in the `prompt` you compose — and you must not drop the attribution metadata from `prior_findings` (don't flatten findings to bare content strings).

Requirement 6 is graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/3.3
pip install -r requirements.txt
pytest -v
```

No `ANTHROPIC_API_KEY` needed — the exercise is pure logic.

When you're ready (or stuck), run `/verify 3.3` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first.
- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — the Agent/Task tool, `allowed_tools`, and `AgentDefinition` fields.
- [Agent SDK — Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) — fork-based session management.
