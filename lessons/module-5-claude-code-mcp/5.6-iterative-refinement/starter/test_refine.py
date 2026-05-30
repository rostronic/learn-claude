from refine import should_keep_iterating, next_context_action


def test_stops_when_check_passes():
    assert should_keep_iterating(check_passed=True, attempts=1, max_attempts=5) is False


def test_keeps_going_while_failing_under_cap():
    assert should_keep_iterating(check_passed=False, attempts=2, max_attempts=5) is True


def test_stops_at_cap_even_if_failing():
    # safety net: don't spin forever
    assert should_keep_iterating(check_passed=False, attempts=5, max_attempts=5) is False


def test_passing_overrides_remaining_budget():
    assert should_keep_iterating(check_passed=True, attempts=0, max_attempts=5) is False


def test_continue_when_healthy():
    assert next_context_action(same_issue_corrections=1,
                               switching_to_unrelated_task=False) == "continue"


def test_clear_on_unrelated_task_switch():
    assert next_context_action(same_issue_corrections=0,
                               switching_to_unrelated_task=True) == "clear"


def test_clear_after_more_than_two_corrections():
    assert next_context_action(same_issue_corrections=3,
                               switching_to_unrelated_task=False) == "clear"


def test_two_corrections_is_still_continue():
    # "more than twice" is the threshold; exactly two does not yet trigger a reset
    assert next_context_action(same_issue_corrections=2,
                               switching_to_unrelated_task=False) == "continue"
