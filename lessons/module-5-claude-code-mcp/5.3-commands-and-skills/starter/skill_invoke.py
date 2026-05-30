"""Pure-logic model of skill argument expansion and invocation control.

No Claude Code process, no API. You implement two behaviors documented in the
skills reference: expanding argument placeholders in a skill body, and deciding
who may invoke a skill given its frontmatter flags. The tests encode the contract.
"""


def expand_arguments(body, args):
    """Expand argument placeholders in a skill body.

    Placeholders (per the skills docs):
      - "$ARGUMENTS" -> all args joined by a single space.
      - "$1", "$2", ... "$9" -> the 1-based positional argument, or "" if there
        is no such argument.

    Args:
        body: the skill body text containing placeholders.
        args: list of positional argument strings (may be empty).

    Rules:
      - Replace every occurrence of "$ARGUMENTS" with " ".join(args).
      - Replace "$1".."$9" with the corresponding arg (args[0] for $1), or "" if
        out of range.
      - Leave all other text unchanged. Do not touch a bare "$" or "$0".

    Example:
      expand_arguments("Fix issue $1 in $2", ["123", "auth.py"])
        -> "Fix issue 123 in auth.py"
      expand_arguments("All: $ARGUMENTS", ["a", "b"]) -> "All: a b"

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement expand_arguments")


def can_invoke(skill, actor):
    """Return True if `actor` may invoke `skill`, per invocation-control rules.

    Args:
        skill: a dict that may contain the boolean frontmatter flags
            "disable_model_invocation" (default False) and
            "user_invocable" (default True).
        actor: either "user" or "model".

    Documented rules:
      - Default (no flags): both "user" and "model" can invoke.
      - disable_model_invocation == True: "user" can, "model" cannot.
      - user_invocable == False: "model" can, "user" cannot.
      (If both restrictions are set, neither can invoke.)

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement can_invoke")
