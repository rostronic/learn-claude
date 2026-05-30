"""Capstone: validate a Developer-Productivity rollout plan.

This is a DESIGN/ANALYSIS exercise. You don't call any API or run Claude Code; you
encode the requirement -> mechanism mapping from the lesson as a checkable plan, and
a validator confirms each requirement is met with the Anthropic-prescribed mechanism
(and that none of the module's anti-patterns slipped in).

You implement `validate_plan(plan)`. A `plan` is a dict mapping each requirement key
to your chosen mechanism (a dict). The validator returns a list of human-readable
problem strings; an empty list means the plan is correct.

Requirement keys and what the CORRECT choice looks like (see the lesson):

  "repo_conventions":     {"location": "project_claude_md"}
  "language_rules":       {"mechanism": "path_rule", "paths": [<non-empty globs>]}
  "no_edit_generated":    {"mechanism": "hook", "event": "PreToolUse", "blocks": True}
  "deploy_workflow":      {"mechanism": "skill", "disable_model_invocation": True}
  "shared_database":      {"mechanism": "mcp", "scope": "project",
                           "secret_in_file": False}
  "ci_review":            {"mechanism": "github_action",
                           "api_key": "${{ secrets.ANTHROPIC_API_KEY }}"}

The validator must flag the anti-patterns, e.g.:
  - repo conventions placed in user memory or a single monolithic location other
    than the project CLAUDE.md,
  - language rules without path scoping (would bloat every session),
  - the no-edit rule expressed as a CLAUDE.md instruction instead of a blocking hook,
  - a deploy skill that the model can auto-invoke,
  - an MCP server not shared at project scope, or with the secret committed in-file,
  - a CI api_key that is a hard-coded literal instead of a secrets reference.
"""

import re

SECRET_REF = re.compile(r"^\$\{\{\s*secrets\.[A-Za-z_][A-Za-z0-9_]*\s*\}\}$")


def validate_plan(plan):
    """Return a list of problem strings; empty list means the plan is valid.

    Implement one check per requirement key per the contract above. Each violated
    requirement contributes at least one problem string. A missing required key is
    itself a problem.

    Suggested problem-string convention (the tests only check WHICH requirement is
    flagged, via substring match on the requirement key, so include the key name):
      e.g. "repo_conventions: must live in the project CLAUDE.md"

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement validate_plan")
