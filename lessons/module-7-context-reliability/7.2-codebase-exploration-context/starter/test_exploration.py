"""Tests for the codebase-exploration context helpers.

Deterministic and offline: no Anthropic API, no network, no API key needed.
Run from this directory with:  pytest test_exploration.py -v
"""

from exploration import select_files, trim_output, order_by_relevance
from fixtures import REPO_INDEX, make_long_text


# --- search-first: select_files returns a ranked SUBSET ---------------------

def test_select_files_returns_subset_not_everything():
    # The index has 10 entries; a search must return a proper subset.
    result = select_files("user login and session", REPO_INDEX, max_files=5)
    assert len(result) <= 5
    assert len(result) < len(REPO_INDEX), "must not return the whole index"


def test_select_files_respects_max_files():
    result = select_files("user login and session", REPO_INDEX, max_files=2)
    assert len(result) <= 2


def test_select_files_ranks_relevant_first():
    # An auth/session query should surface the auth files ahead of anything else.
    result = select_files("user login and session", REPO_INDEX, max_files=3)
    assert "auth/login.py" in result
    # The most-overlapping file should lead.
    assert result[0] == "auth/login.py"


def test_select_files_excludes_irrelevant_entries():
    result = select_files("user login and session", REPO_INDEX, max_files=5)
    # Nothing about billing/search should be pulled in by an auth query.
    assert "billing/invoice.py" not in result
    assert "search/indexer.py" not in result


def test_select_files_returns_paths_from_index():
    result = select_files("payment refund", REPO_INDEX, max_files=3)
    known_paths = {entry["path"] for entry in REPO_INDEX}
    for path in result:
        assert path in known_paths


# --- trim_output: cap long text, leave short text alone ---------------------

def test_trim_output_caps_long_text_and_marks_truncation():
    text = make_long_text(200)
    trimmed = trim_output(text, max_lines=50)
    lines = trimmed.splitlines()
    # 50 kept lines + 1 truncation marker line.
    assert len(lines) == 51
    assert lines[:50] == text.splitlines()[:50]
    assert "truncated" in lines[-1].lower()
    assert "150" in lines[-1], "marker should report the number of dropped lines"


def test_trim_output_leaves_short_text_unchanged():
    text = make_long_text(10)
    assert trim_output(text, max_lines=50) == text


def test_trim_output_boundary_equal_to_max_is_unchanged():
    text = make_long_text(50)
    assert trim_output(text, max_lines=50) == text


# --- order_by_relevance: sort by score descending --------------------------

def test_order_by_relevance_sorts_desc():
    chunks = [
        {"path": "ui/dashboard.py", "score": 1},
        {"path": "auth/login.py", "score": 9},
        {"path": "auth/tokens.py", "score": 6},
    ]
    ordered = order_by_relevance(chunks)
    scores = [c["score"] for c in ordered]
    assert scores == [9, 6, 1]
    assert ordered[0]["path"] == "auth/login.py"


def test_order_by_relevance_keeps_all_chunks():
    chunks = [{"path": "a", "score": 2}, {"path": "b", "score": 5}]
    ordered = order_by_relevance(chunks)
    assert len(ordered) == len(chunks)
