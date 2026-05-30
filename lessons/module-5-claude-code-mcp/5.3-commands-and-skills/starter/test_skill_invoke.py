from skill_invoke import expand_arguments, can_invoke


def test_arguments_joins_all():
    assert expand_arguments("All: $ARGUMENTS", ["a", "b"]) == "All: a b"


def test_positional_substitution():
    assert expand_arguments("Fix $1 in $2", ["123", "auth.py"]) == "Fix 123 in auth.py"


def test_missing_positional_becomes_empty():
    assert expand_arguments("x=$1 y=$2", ["only"]) == "x=only y="


def test_other_text_untouched_and_no_dollar0():
    assert expand_arguments("price is $ and $0 stays", ["a"]) == "price is $ and $0 stays"


def test_default_skill_both_can_invoke():
    skill = {"name": "review"}
    assert can_invoke(skill, "user") is True
    assert can_invoke(skill, "model") is True


def test_disable_model_invocation_user_only():
    skill = {"name": "deploy", "disable_model_invocation": True}
    assert can_invoke(skill, "user") is True
    assert can_invoke(skill, "model") is False


def test_user_invocable_false_model_only():
    skill = {"name": "legacy-context", "user_invocable": False}
    assert can_invoke(skill, "user") is False
    assert can_invoke(skill, "model") is True


def test_both_restrictions_block_everyone():
    skill = {"name": "x", "disable_model_invocation": True, "user_invocable": False}
    assert can_invoke(skill, "user") is False
    assert can_invoke(skill, "model") is False
