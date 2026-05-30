from plan_decision import should_use_plan_mode, plan_mode_allows


def _task(approach_uncertain=False, files_touched=1, unfamiliar_code=False):
    return {
        "approach_uncertain": approach_uncertain,
        "files_touched": files_touched,
        "unfamiliar_code": unfamiliar_code,
    }


def test_one_sentence_diff_acts_directly():
    # typo / log line: clear, single file, familiar
    assert should_use_plan_mode(_task()) is False


def test_multi_file_triggers_plan():
    assert should_use_plan_mode(_task(files_touched=5)) is True


def test_uncertain_approach_triggers_plan():
    assert should_use_plan_mode(_task(approach_uncertain=True)) is True


def test_unfamiliar_code_triggers_plan():
    assert should_use_plan_mode(_task(unfamiliar_code=True)) is True


def test_any_trigger_is_enough():
    # multiple triggers at once still plans
    assert should_use_plan_mode(
        _task(approach_uncertain=True, files_touched=8, unfamiliar_code=True)
    ) is True


def test_plan_mode_allows_reads():
    assert plan_mode_allows(is_mutating=False) is True


def test_plan_mode_blocks_edits():
    assert plan_mode_allows(is_mutating=True) is False
