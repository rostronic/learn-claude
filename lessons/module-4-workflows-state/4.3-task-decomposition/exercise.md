# Task decomposition strategies — exercise

## What you're building

A small planner that decomposes a complex task ("review this PR") into subagent
specs, validates a plan for the structural mistakes the exam tests, and groups
the work into ordered parallel batches. Each spec is a plain dict standing in for
an Agent SDK `AgentDefinition`.

## Function signatures

```python
READ_ONLY = ["Read", "Grep", "Glob"]
TEST_RUNNER = ["Bash", "Read", "Grep"]

def decompose(task):
    """Return a list of subtask specs:
        {"name": str, "tools": list[str], "depends_on": list[str], "parallel_group": int}"""

def validate_plan(plan):
    """Return a list of problem strings (empty = valid)."""

def parallel_batches(plan):
    """Return a list of lists of names, ordered by parallel_group."""
```

## Requirements

You must:

1. **In `decompose`, produce three independent read-only finders** — `style-checker`, `security-scanner`, `test-runner` — in `parallel_group` 0 with `depends_on == []`, plus a `synthesis` step in `parallel_group` 1 that `depends_on` all three finders.
2. **Apply least-privilege tools:** `style-checker` and `security-scanner` get exactly `["Read", "Grep", "Glob"]`; `test-runner` gets `Bash` (it executes tests); `synthesis` is read-only.
3. **Never put `"Agent"` in any spec's `tools`** — subagents cannot spawn subagents.
4. **In `validate_plan`, flag** (each as a problem string): any spec whose `tools` include `"Agent"`; any `depends_on` referencing an unknown subtask name; any dependency inversion (a spec depending on another in the **same or a later** `parallel_group`). Return `[]` for a valid plan.
5. **In `parallel_batches`, group names by `parallel_group`** into ordered batches (batch *i* runs after batch *i*−1).
6. **Pass every test in `test_decompose.py`.**

You must NOT:

7. **Grant the `"Agent"` tool to any subtask** (the one-level decomposition rule). Your `decompose` output must never include it, and `validate_plan` must catch it when present.
8. **Place a dependent subtask in the same or an earlier batch than its dependency** (a dependency inversion), or give a read-only analyzer write/exec tools it doesn't need.

Requirements 7 and 8 are graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/4.3
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — no Anthropic client, no `ANTHROPIC_API_KEY`, no API
credits. The specs map directly onto `ClaudeAgentOptions(agents={name:
AgentDefinition(...)})` if you later wire them into a real run
(`pip install claude-agent-sdk`).

When you're ready (or stuck), run `/verify 4.3` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — `AgentDefinition`, least-privilege `tools`, and the rule that subagents cannot spawn subagents.
- [Agent SDK — dynamic workflows](https://code.claude.com/docs/en/workflows) — scaling decomposition past a handful of subagents.
