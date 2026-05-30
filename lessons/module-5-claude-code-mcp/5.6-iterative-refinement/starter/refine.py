"""Pure-logic model of two iterative-refinement decisions.

No Claude Code process, no API. You implement the verify-driven iteration rule and
the context-hygiene decision documented in the best-practices guide. The tests
encode the contract.
"""


def should_keep_iterating(check_passed, attempts, max_attempts):
    """Return True if the refinement loop should run another iteration.

    The real stop signal is the CHECK passing; the attempt cap is only a runaway
    guard (mirrors stop_reason vs an iteration cap in agentic loops).

    Keep iterating IFF the check has not yet passed AND we are still under the cap:
      return (not check_passed) and (attempts < max_attempts)

    Args:
        check_passed: True if the test/build/screenshot check passed.
        attempts: how many iterations have already run.
        max_attempts: the safety cap.

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement should_keep_iterating")


def next_context_action(same_issue_corrections, switching_to_unrelated_task):
    """Decide the recommended context-management action for the session.

    Documented rules:
      - Reset between unrelated tasks: if switching_to_unrelated_task is True,
        return "clear".
      - Reset after repeated correction: if you've corrected Claude MORE THAN TWICE
        on the same issue (same_issue_corrections > 2), return "clear" and restart
        with a sharper prompt.
      - Otherwise return "continue".

    Return one of the strings "clear" or "continue".

    TODO (exercise): implement this.
    """
    raise NotImplementedError("implement next_context_action")
