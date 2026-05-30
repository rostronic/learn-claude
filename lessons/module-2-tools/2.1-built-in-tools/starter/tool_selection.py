"""Starter skeleton for Learn Claude chapter 2.1 — Built-in tools.

Implement the three functions below. See exercise.md for the full spec.
These are pure logic — no Anthropic API, no API key, no network.
"""


def select_tool(intent: str) -> str:
    """Return the built-in tool name for a described file operation.

    Intent -> tool:
      "read_file"                    -> "Read"
      "find_files_by_name"           -> "Glob"
      "search_file_contents"         -> "Grep"
      "edit_region_of_existing_file" -> "Edit"
      "create_or_overwrite_file"     -> "Write"
      "run_command"                  -> "Bash"

    Raise ValueError for an unknown intent.
    """
    # TODO: implement. Map each intent to its purpose-built tool.
    #   Do NOT return "Bash" for read_file / find_files_by_name /
    #   search_file_contents — those have dedicated tools.
    raise NotImplementedError("Implement select_tool — see exercise.md")


def requires_permission(tool: str) -> bool:
    """True if the built-in tool requires permission, False otherwise.

    Requires permission: Bash, Edit, Write, WebFetch, WebSearch, NotebookEdit.
    No permission: Read, Grep, Glob.
    Raise ValueError for an unknown tool.
    """
    # TODO: implement per the Tools-reference permission column.
    raise NotImplementedError("Implement requires_permission — see exercise.md")


def plan_is_safe(operations: list) -> bool:
    """Validate a plan against the read-before-edit rule.

    Each operation is a dict: {"tool": <name>, "path": <str>}.
    An "Edit" or "Write" on a path is safe only if a "Read" of that same path
    appears earlier in the plan. Return True if every Edit/Write is preceded by
    a Read of its path; False otherwise.
    """
    # TODO: implement. Track which paths have been Read so far as you scan
    #   the operations in order; an Edit/Write to an unread path is unsafe.
    raise NotImplementedError("Implement plan_is_safe — see exercise.md")
