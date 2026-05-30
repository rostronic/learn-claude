from rule_matcher import glob_match, active_rules


def test_doublestar_matches_nested_segments():
    assert glob_match("**/*.ts", "app.ts")
    assert glob_match("**/*.ts", "src/app.ts")
    assert glob_match("**/*.ts", "src/api/deep.ts")


def test_single_star_stays_within_a_segment():
    assert glob_match("*.md", "README.md")
    assert not glob_match("*.md", "docs/README.md")
    assert glob_match("src/components/*.tsx", "src/components/Btn.tsx")
    assert not glob_match("src/components/*.tsx", "src/components/x/Btn.tsx")


def test_prefix_doublestar():
    assert glob_match("src/**/*", "src/api/handler.ts")
    assert glob_match("src/**/*", "src/x.ts")
    assert not glob_match("src/**/*", "lib/x.ts")


def test_doublestar_does_not_leak_across_a_different_prefix():
    assert glob_match("migrations/**", "migrations/001.sql")
    assert glob_match("migrations/**", "migrations/sub/2.sql")
    assert not glob_match("migrations/**", "app/migrations.py")


def test_brace_like_separate_patterns_via_match():
    # extension matching within one segment
    assert glob_match("src/**/*.test.ts", "src/a/b/x.test.ts")
    assert not glob_match("src/**/*.test.ts", "src/a/x.ts")


def test_unconditional_rule_always_active():
    rules = [
        {"name": "global-style", "paths": None},
        {"name": "api", "paths": ["src/api/**/*.ts"]},
    ]
    assert active_rules("README.md", rules) == ["global-style"]
    assert active_rules("src/api/users.ts", rules) == ["global-style", "api"]


def test_path_scoped_rule_only_when_matching():
    rules = [
        {"name": "api", "paths": ["src/api/**/*.ts"]},
        {"name": "tests", "paths": ["tests/**/*.test.ts"]},
    ]
    assert active_rules("src/api/users.ts", rules) == ["api"]
    assert active_rules("tests/users.test.ts", rules) == ["tests"]
    assert active_rules("src/web/app.tsx", rules) == []


def test_multiple_globs_any_match_activates():
    rules = [{"name": "frontend", "paths": ["src/**/*.tsx", "lib/**/*.ts"]}]
    assert active_rules("src/web/App.tsx", rules) == ["frontend"]
    assert active_rules("lib/util.ts", rules) == ["frontend"]
    assert active_rules("src/web/App.ts", rules) == []


def test_order_is_preserved():
    rules = [
        {"name": "a", "paths": None},
        {"name": "b", "paths": ["**/*.py"]},
        {"name": "c", "paths": None},
    ]
    assert active_rules("x.py", rules) == ["a", "b", "c"]
