import pytest

from mcp_config import resolve_server, expand_env


def test_local_wins_over_project_and_user():
    by_scope = {
        "local": {"db": {"url": "local"}},
        "project": {"db": {"url": "project"}},
        "user": {"db": {"url": "user"}},
    }
    assert resolve_server("db", by_scope) == {"url": "local"}


def test_project_wins_over_user():
    by_scope = {
        "project": {"db": {"url": "project"}},
        "user": {"db": {"url": "user"}},
    }
    assert resolve_server("db", by_scope) == {"url": "project"}


def test_no_field_merging_across_scopes():
    by_scope = {
        "local": {"db": {"url": "local"}},          # no "headers"
        "user": {"db": {"url": "user", "headers": {"k": "v"}}},
    }
    # local wins entirely; user's headers are NOT merged in
    assert resolve_server("db", by_scope) == {"url": "local"}


def test_missing_server_returns_none():
    assert resolve_server("nope", {"user": {"db": {}}}) is None


def test_expand_simple_var():
    assert expand_env("${A}/mcp", {"A": "x"}) == "x/mcp"


def test_expand_with_default_used():
    assert expand_env("${A:-def}", {}) == "def"


def test_expand_with_default_overridden():
    assert expand_env("${A:-def}", {"A": "real"}) == "real"


def test_expand_multiple_placeholders():
    assert expand_env("${A}-${B}", {"A": "1", "B": "2"}) == "1-2"


def test_missing_required_var_raises():
    with pytest.raises(KeyError):
        expand_env("${MISSING}", {})


def test_plain_text_unchanged():
    assert expand_env("no placeholders here", {}) == "no placeholders here"
