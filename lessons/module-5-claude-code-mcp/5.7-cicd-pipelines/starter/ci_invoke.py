"""Pure-logic model of two CI/CD integration behaviors.

No Claude Code process, no API. You implement a secret-reference check (the #1 CI
security rule) and a headless-command builder (the `claude -p` invocation). The
tests encode the contract.
"""

import re


def is_secret_reference(value):
    """Return True iff `value` is a GitHub Actions secret reference, not a literal.

    A safe reference looks like "${{ secrets.NAME }}" (optional surrounding
    whitespace inside the braces); NAME matches [A-Za-z_][A-Za-z0-9_]*.

    A hard-coded key (e.g. "sk-ant-abc123") is NOT a secret reference and must
    return False — that's the value you must never commit.

    Examples:
      is_secret_reference("${{ secrets.ANTHROPIC_API_KEY }}") -> True
      is_secret_reference("${{secrets.TOKEN}}")               -> True
      is_secret_reference("sk-ant-abc123")                    -> False
      is_secret_reference("${{ env.FOO }}")                   -> False

    TODO (exercise): implement this (a regex is fine).
    """
    raise NotImplementedError("implement is_secret_reference")


def build_headless_command(prompt, *, allowed_tools=None, output_format="text",
                           permission_mode=None):
    """Build the argv list for a non-interactive `claude -p` invocation.

    Start from ["claude", "-p", prompt], then append flags IN THIS ORDER, each only
    when it applies:
      - allowed_tools: a list of tool names -> ["--allowedTools", ",".join(tools)]
        (omit entirely if None or empty).
      - output_format: -> ["--output-format", output_format] only when it is NOT
        "text" (the default needs no flag).
      - permission_mode: -> ["--permission-mode", permission_mode] when truthy.

    Return the argv as a list of strings.

    Example:
      build_headless_command("fix tests", allowed_tools=["Read", "Edit"],
                             output_format="json", permission_mode="dontAsk")
        -> ["claude", "-p", "fix tests",
            "--allowedTools", "Read,Edit",
            "--output-format", "json",
            "--permission-mode", "dontAsk"]

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement build_headless_command")
