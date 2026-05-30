from rollout_plan import validate_plan


def good_plan():
    return {
        "repo_conventions": {"location": "project_claude_md"},
        "language_rules": {"mechanism": "path_rule", "paths": ["**/*.py"]},
        "no_edit_generated": {"mechanism": "hook", "event": "PreToolUse",
                              "blocks": True},
        "deploy_workflow": {"mechanism": "skill",
                            "disable_model_invocation": True},
        "shared_database": {"mechanism": "mcp", "scope": "project",
                            "secret_in_file": False},
        "ci_review": {"mechanism": "github_action",
                      "api_key": "${{ secrets.ANTHROPIC_API_KEY }}"},
    }


def _flagged(problems, key):
    return any(key in p for p in problems)


def test_correct_plan_has_no_problems():
    assert validate_plan(good_plan()) == []


def test_repo_conventions_in_user_memory_flagged():
    p = good_plan()
    p["repo_conventions"] = {"location": "user_claude_md"}
    assert _flagged(validate_plan(p), "repo_conventions")


def test_language_rules_without_paths_flagged():
    p = good_plan()
    p["language_rules"] = {"mechanism": "path_rule", "paths": []}
    assert _flagged(validate_plan(p), "language_rules")


def test_language_rules_in_root_claude_md_flagged():
    p = good_plan()
    p["language_rules"] = {"mechanism": "project_claude_md"}
    assert _flagged(validate_plan(p), "language_rules")


def test_no_edit_rule_as_prompt_flagged():
    p = good_plan()
    p["no_edit_generated"] = {"mechanism": "claude_md_instruction"}
    assert _flagged(validate_plan(p), "no_edit_generated")


def test_non_blocking_hook_flagged():
    p = good_plan()
    p["no_edit_generated"] = {"mechanism": "hook", "event": "PreToolUse",
                              "blocks": False}
    assert _flagged(validate_plan(p), "no_edit_generated")


def test_deploy_skill_model_invocable_flagged():
    p = good_plan()
    p["deploy_workflow"] = {"mechanism": "skill",
                            "disable_model_invocation": False}
    assert _flagged(validate_plan(p), "deploy_workflow")


def test_database_local_scope_flagged():
    p = good_plan()
    p["shared_database"] = {"mechanism": "mcp", "scope": "local",
                            "secret_in_file": False}
    assert _flagged(validate_plan(p), "shared_database")


def test_database_secret_in_file_flagged():
    p = good_plan()
    p["shared_database"] = {"mechanism": "mcp", "scope": "project",
                            "secret_in_file": True}
    assert _flagged(validate_plan(p), "shared_database")


def test_ci_hardcoded_key_flagged():
    p = good_plan()
    p["ci_review"] = {"mechanism": "github_action", "api_key": "sk-ant-abc123"}
    assert _flagged(validate_plan(p), "ci_review")


def test_missing_requirement_flagged():
    p = good_plan()
    del p["deploy_workflow"]
    assert _flagged(validate_plan(p), "deploy_workflow")
