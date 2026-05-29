"""Starter skeleton for Learn Claude chapter 3.4 — Distributing tools across agents.

Implement the three helpers below. See exercise.md for the full spec.
"""


def build_agent_toolset(role, role_tools, max_tools=5):
    """Return the scoped tool list for `role`.

    Args:
        role:       str — the agent role to look up.
        role_tools: dict[str, list[str]] — role -> its allowed tool names.
        max_tools:  int — the maximum tools a single agent should be given.

    Returns:
        list[str] — a COPY of role_tools[role].

    Raises:
        KeyError   if role not in role_tools.
        ValueError if the role's tool list is longer than max_tools.
    """
    # TODO: implement
    #   1. Raise KeyError if role not in role_tools.
    #   2. Raise ValueError if len(role_tools[role]) > max_tools.
    #   3. Return a copy of role_tools[role] (don't hand back the shared list).
    raise NotImplementedError("Implement build_agent_toolset — see exercise.md")


def tool_choice_any():
    """Return the tool_choice that requires the model to call some tool."""
    # TODO: implement
    raise NotImplementedError("Implement tool_choice_any — see exercise.md")


def tool_choice_force(name):
    """Return the tool_choice that forces the named tool."""
    # TODO: implement
    raise NotImplementedError("Implement tool_choice_force — see exercise.md")
