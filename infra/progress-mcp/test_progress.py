"""Tests for the progress-tracking core logic.

These never touch the real repo, the real ~/learn-claude-work, the network, or
the Anthropic API. A temp fake repo (a minimal curriculum map, exam mapping,
and one exam config) and an isolated work dir are wired in via the
LEARN_CLAUDE_REPO / LEARN_CLAUDE_WORK_DIR env vars, so each test round-trips
record_*/get_progress against a throwaway progress.json.

    pip install -r requirements.txt && pytest
"""

import json
import textwrap

import pytest

import progress

CURRICULUM_MD = textwrap.dedent(
    """
    # Curriculum map

    ## Module 3
    | Chapter | Title | Status |
    |---|---|---|
    | 3.1 | Agentic loops | **built** |
    | 3.2 | Coordinator and subagent orchestration | **built** |
    | 4.1 | Multi-step workflows | planned |
    """
).strip()

EXAM_MAPPING_MD = textwrap.dedent(
    """
    ---
    exams:
      CCAF:
        coverage:
          - { task_statement: "1.1 ...", domain: 1, lesson_chapter: "3.1", status: built }
          - { task_statement: "1.2 ...", domain: 1, lesson_chapter: "3.2", status: built }
    ---
    # Exam mapping
    """
).strip()

EXAM_YAML = textwrap.dedent(
    """
    exam: "CCAF"
    passing_score: 720
    domains:
      1: "Agentic Architecture & Orchestration"
      2: "Tool Design & MCP Integration"
      3: "Claude Code Configuration & Workflows"
      4: "Prompt Engineering & Structured Output"
      5: "Context Management & Reliability"
    """
).strip()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A fake repo (docs + one exam) and an isolated, initially-empty work dir."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "curriculum-map.md").write_text(CURRICULUM_MD, encoding="utf-8")
    (repo / "docs" / "exam-mapping.md").write_text(EXAM_MAPPING_MD, encoding="utf-8")
    (repo / "exams" / "CCAF").mkdir(parents=True)
    (repo / "exams" / "CCAF" / "exam.yaml").write_text(EXAM_YAML, encoding="utf-8")

    work = tmp_path / "work"  # deliberately NOT created — tests that need it create it

    monkeypatch.setenv("LEARN_CLAUDE_REPO", str(repo))
    monkeypatch.setenv("LEARN_CLAUDE_WORK_DIR", str(work))
    return type("Env", (), {"repo": repo, "work": work})()


# --------------------------------------------------------------------------- #
# curriculum awareness
# --------------------------------------------------------------------------- #


def test_known_chapters_parses_built_and_planned(env):
    all_chapters, built = progress.known_chapters()
    assert all_chapters == {"3.1", "3.2", "4.1"}
    assert built == {"3.1", "3.2"}  # 4.1 is planned


# --------------------------------------------------------------------------- #
# get_progress: missing vs. empty work dir
# --------------------------------------------------------------------------- #


def test_get_progress_missing_work_dir_is_structured_error(env):
    # The work dir does not exist yet → structured, non-retryable error.
    # The core raises; the MCP wrapper (and CLI) turn it into an envelope.
    assert not env.work.exists()
    with pytest.raises(progress.ProgressError) as ei:
        progress.get_progress()
    assert ei.value.category == "work_dir_missing"
    assert ei.value.retryable is False
    assert ei.value.to_envelope()["error"]["category"] == "work_dir_missing"


def test_get_progress_empty_when_dir_exists_without_file(env):
    env.work.mkdir(parents=True)
    out = progress.get_progress()
    assert "error" not in out
    assert out["chapters"] == {}
    assert out["mock_exams"] == []
    assert out["summary"]["counts"]["chapters_built"] == 2


# --------------------------------------------------------------------------- #
# record_study / record_exercise
# --------------------------------------------------------------------------- #


def test_record_study_creates_file_and_reflects(env):
    assert not progress.progress_path().exists()
    entry = progress.record_study("3.1")
    assert entry["chapter"] == "3.1"
    assert entry["entry"]["studied"] is True
    assert progress.progress_path().exists()

    out = progress.get_progress()
    assert out["chapters"]["3.1"]["studied"] is True
    assert "3.1" in out["summary"]["studied"]
    assert out["updated"] is not None


def test_record_exercise(env):
    progress.record_exercise("3.2")
    out = progress.get_progress()
    assert out["chapters"]["3.2"]["exercised"] is True
    assert out["summary"]["per_chapter"]["3.2"]["exercised"] is True


# --------------------------------------------------------------------------- #
# record_verify (the headline round-trip)
# --------------------------------------------------------------------------- #


def test_record_verify_then_get_progress_reflects_it(env):
    progress.record_verify("3.1", 92)
    out = progress.get_progress()
    verified = out["chapters"]["3.1"]["verified"]
    assert verified["score"] == 92
    assert verified["passed"] is True
    assert "3.1" in out["summary"]["verified_passed"]
    assert out["summary"]["counts"]["verified_passed"] == 1


def test_record_verify_below_threshold_is_not_passed(env):
    progress.record_verify("3.1", 70)
    out = progress.get_progress()
    assert out["chapters"]["3.1"]["verified"]["passed"] is False
    assert out["summary"]["verified_passed"] == []


@pytest.mark.parametrize("bad", [-1, 101, 150, "ninety", True])
def test_record_verify_rejects_out_of_range_score(env, bad):
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_verify("3.1", bad)
    assert ei.value.category == "invalid_score"


# --------------------------------------------------------------------------- #
# chapter validation
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad", ["3", "3.", "abc", "3.1.2", "", "lessons/3.1"])
def test_invalid_chapter_format(env, bad):
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_study(bad)
    assert ei.value.category == "invalid_chapter"


def test_unknown_chapter_rejected(env):
    # Well-formed but absent from the curriculum map.
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_study("9.9")
    assert ei.value.category == "unknown_chapter"
    assert ei.value.retryable is False


# --------------------------------------------------------------------------- #
# record_practice
# --------------------------------------------------------------------------- #


def test_record_practice_appends(env):
    progress.record_practice("3.1", True)
    progress.record_practice("3.1", False)
    out = progress.get_progress()
    attempts = out["practice"]["3.1"]
    assert [a["correct"] for a in attempts] == [True, False]
    pc = out["summary"]["per_chapter"]["3.1"]
    assert pc["practice_attempts"] == 2
    assert pc["practice_correct"] == 1


def test_record_practice_rejects_non_bool(env):
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_practice("3.1", "yes")
    assert ei.value.category == "invalid_input"


# --------------------------------------------------------------------------- #
# record_mock + weak-domain derivation
# --------------------------------------------------------------------------- #


def test_record_mock_and_weak_domains_sorted(env):
    progress.record_mock(
        "CCAF", 760, True, {"1": 0.9, "2": 0.6, "5": 0.4}
    )
    out = progress.get_progress()
    latest = out["summary"]["latest_mock"]
    assert latest["scaled"] == 760
    assert latest["pass"] is True

    weak = out["summary"]["weak_domains"]
    # Lowest ratio first; domain 5 is weakest.
    assert [w["domain"] for w in weak] == ["5", "2", "1"]
    # Name resolved from the fake exam.yaml.
    assert weak[0]["name"] == "Context Management & Reliability"


def test_record_mock_appends_history(env):
    progress.record_mock("CCAF", 600, False, {"1": 0.5})
    progress.record_mock("CCAF", 780, True, {"1": 0.9})
    out = progress.get_progress()
    assert len(out["mock_exams"]) == 2
    assert out["summary"]["latest_mock"]["scaled"] == 780


def test_record_mock_rejects_bad_scaled(env):
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_mock("CCAF", 2000, True, {"1": 0.9})
    assert ei.value.category == "invalid_scaled"


def test_record_mock_rejects_bad_per_domain(env):
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_mock("CCAF", 760, True, {"1": 1.5})
    assert ei.value.category == "invalid_per_domain"


def test_record_mock_unknown_exam(env):
    with pytest.raises(progress.ProgressError) as ei:
        progress.record_mock("ZZZ", 760, True, {"1": 0.9})
    assert ei.value.category == "unknown_exam"


# --------------------------------------------------------------------------- #
# recommended_next
# --------------------------------------------------------------------------- #


def test_recommend_next_points_at_unstudied_built_chapter(env):
    progress.record_study("3.1")  # 3.2 is built but unstudied
    rec = progress.get_progress()["summary"]["recommended_next"]
    assert rec["action"] == "study"
    assert rec["chapter"] == "3.2"


def test_recommend_next_verify_after_study(env):
    progress.record_study("3.1")
    progress.record_study("3.2")  # both built chapters studied, none verified
    rec = progress.get_progress()["summary"]["recommended_next"]
    assert rec["action"] in {"exercise", "verify"}
    assert rec["chapter"] in {"3.1", "3.2"}


# --------------------------------------------------------------------------- #
# corruption + envelope shape
# --------------------------------------------------------------------------- #


def test_corrupt_progress_file_is_structured_error(env):
    env.work.mkdir(parents=True)
    progress.progress_path().write_text("{not json", encoding="utf-8")
    with pytest.raises(progress.ProgressError) as ei:
        progress.get_progress()
    assert ei.value.category == "progress_corrupt"


def test_error_envelope_shape():
    err = progress.ProgressError("work_dir_missing", "nope", retryable=False, hint="do x")
    assert err.to_envelope() == {
        "error": {
            "category": "work_dir_missing",
            "message": "nope",
            "retryable": False,
            "hint": "do x",
        }
    }


def test_error_envelope_omits_absent_hint():
    err = progress.ProgressError("invalid_score", "bad", retryable=False)
    assert "hint" not in err.to_envelope()["error"]


# --------------------------------------------------------------------------- #
# CLI (the Bash fallback)
# --------------------------------------------------------------------------- #


def test_cli_round_trip(env, capsys):
    assert progress._cli(["verify", "3.1", "92"]) == 0
    capsys.readouterr()  # drain
    assert progress._cli(["get"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["chapters"]["3.1"]["verified"]["score"] == 92


def test_cli_bad_chapter_returns_envelope_and_nonzero(env, capsys):
    code = progress._cli(["study", "abc"])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["category"] == "invalid_chapter"


def test_cli_missing_work_dir_returns_envelope(env, capsys):
    assert not env.work.exists()
    code = progress._cli(["get"])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["category"] == "work_dir_missing"
