# Distributing tools across agents & tool choice — exercise

## What you're building

Implement three helpers in `tool_distribution.py`: scope an agent's toolset to its role (refusing to over-provision), and construct the two `tool_choice` values that force a tool call.

Pure logic — no API calls.

## Function signatures

```python
def build_agent_toolset(role, role_tools, max_tools=5):
    """Return a copy of role_tools[role]. Raise KeyError if role is unknown,
    or ValueError if the role has more than max_tools tools."""

def tool_choice_any():
    """Return {"type": "any"} — the model must call some tool."""

def tool_choice_force(name):
    """Return {"type": "tool", "name": name} — the model must call this specific tool."""
```

## Requirements

You must:

1. **Reject unknown roles.** `build_agent_toolset` raises `KeyError` if `role` isn't in `role_tools`.
2. **Cap the toolset.** Raise `ValueError` if the role's tool list exceeds `max_tools` — too many tools degrades selection reliability.
3. **Return a scoped copy.** Return a *copy* of the role's tool list (not the shared structure), containing exactly that role's tools.
4. **`tool_choice` constructors** return `{"type": "any"}` and `{"type": "tool", "name": name}` respectively.
5. **Pass every test in `test_tool_distribution.py`.**

You must NOT:

6. **Over-provision an agent** — don't return the full registry, tools beyond the role's scope, or bypass the `max_tools` cap. Scope tools tightly to the role.

Requirement 6 is graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/3.4
pip install -r requirements.txt
pytest -v
```

No `ANTHROPIC_API_KEY` needed — the exercise is pure logic.

When you're ready (or stuck), run `/verify 3.4` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first.
- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — the `tools` restriction field.
- [Tool use with Claude](https://platform.claude.com/docs/en/build-with-claude/tool-use) — the `tool_choice` modes.
