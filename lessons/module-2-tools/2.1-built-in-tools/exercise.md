# Built-in tools (Read, Write, Edit, Bash, Grep, Glob) — exercise

## What you're building

A small **tool-selection layer** in `tool_selection.py`: pure logic that, given a described file operation, names the correct built-in tool — and that knows which tools need permission and enforces read-before-edit. This is CCAF Task Statement 2.5 made concrete: choosing the purpose-built tool over a generic `Bash` equivalent.

No Anthropic API is involved — the tests are pure logic and need no `ANTHROPIC_API_KEY`.

## Functions to implement

```python
def select_tool(intent: str) -> str:
    """Return the built-in tool name for a described operation.

    Intents and their correct tools:
      "read_file"                    -> "Read"
      "find_files_by_name"           -> "Glob"
      "search_file_contents"         -> "Grep"
      "edit_region_of_existing_file" -> "Edit"
      "create_or_overwrite_file"     -> "Write"
      "run_command"                  -> "Bash"
    Raise ValueError for an unknown intent.
    """

def requires_permission(tool: str) -> bool:
    """True if the built-in tool requires permission, False otherwise.

    Per the Tools reference: Bash, Edit, Write, WebFetch, WebSearch,
    NotebookEdit require permission; Read, Grep, Glob do not.
    Raise ValueError for an unknown tool.
    """

def plan_is_safe(operations: list[dict]) -> bool:
    """Validate a plan against the read-before-edit rule.

    Each operation is a dict: {"tool": <name>, "path": <str>}.
    An "Edit" or "Write" on a path is only safe if a "Read" of that same
    path appears earlier in the plan. Return True if every Edit/Write is
    preceded by a Read of its path; False otherwise. (Creating a brand-new
    path with Write is out of scope here — assume every Write targets an
    existing file, matching the Tools-reference overwrite rule.)
    """
```

## Requirements

You must:

1. **Map every intent to the correct tool** in `select_tool` — `Grep` for content search, `Glob` for name search, `Read` to read, `Edit` for targeted edits, `Write` for create/overwrite, `Bash` for commands.
2. **Return the correct permission posture** in `requires_permission` — read-only navigation tools (`Read`/`Grep`/`Glob`) are `False`; mutating/escaping tools (`Bash`/`Edit`/`Write`/...) are `True`.
3. **Enforce read-before-edit** in `plan_is_safe` — an `Edit`/`Write` to a path is safe only if a `Read` of that path appeared earlier.
4. **Raise `ValueError`** on unknown intents (in `select_tool`) and unknown tools (in `requires_permission`).
5. **Pass every test in `test_tool_selection.py`.**

You must NOT:

6. **Route file reads, content search, or name search to `Bash`.** `select_tool("read_file")` must be `"Read"`, `select_tool("search_file_contents")` must be `"Grep"`, and `select_tool("find_files_by_name")` must be `"Glob"` — never `"Bash"`. Using the shell escape hatch for a job a dedicated tool already does is the anti-pattern this chapter warns about, and it's graded directly (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/2.1
pip install -r requirements.txt
pytest -v
```

The tests are pure logic — no API key, no network, no credits burned.

When you're ready (or stuck), run `/verify 2.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Claude Code — Tools reference](https://code.claude.com/docs/en/tools-reference) — the built-in tool table, the permission column, and the per-tool behavior (including read-before-edit on `Edit`/`Write`).
