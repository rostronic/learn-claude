"""Pure-logic model of the plan-mode-vs-direct decision and what plan mode permits.

No Claude Code process, no API. You implement the documented heuristic for choosing
plan mode and the rule for what plan mode allows. The tests encode the contract.
"""


def should_use_plan_mode(task):
    """Return True if the task warrants plan mode, per the documented heuristic.

    `task` is a dict with boolean-ish fields:
      - "approach_uncertain": you're unsure of the approach.
      - "files_touched": integer count of files the change spans.
      - "unfamiliar_code": you don't know the code being modified.

    Rule (from best practices): plan when ANY of these hold —
      - approach_uncertain is True, OR
      - files_touched > 1, OR
      - unfamiliar_code is True.
    Otherwise (clear scope, single file, familiar — a one-sentence diff) act
    directly: return False.

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement should_use_plan_mode")


def plan_mode_allows(is_mutating):
    """Return True if an action is permitted in plan mode.

    Plan mode is read/analyze-only: it permits non-mutating actions (reading files,
    grep/glob, read-only exploration) and does NOT permit actions that modify your
    source (file edits/writes).

    Args:
        is_mutating: True if the action would modify the working tree
            (Edit/Write), False for a read-only action.

    Return True iff the action is allowed in plan mode (i.e. NOT mutating).

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement plan_mode_allows")
