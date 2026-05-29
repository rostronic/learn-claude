"""Tests for the grading core logic.

These never touch the real repo, the real ~/learn-claude-work, the network, or
(except where explicitly testing it) a real subprocess. A temp fake repo and
work dir are wired in via the LEARN_CLAUDE_REPO / LEARN_CLAUDE_WORK_DIR env
vars, and subprocess.run is monkeypatched for the bash-check tests.

    pip install -r requirements.txt && pytest
"""

import subprocess
import textwrap
from types import SimpleNamespace

import pytest

import grading

RUBRIC_YAML = textwrap.dedent(
    """
    chapter: "9.9"
    criteria:
      - id: does_the_thing
        description: "Code does the thing"
        weight: 60
        check: code_review
      - id: no_forbidden_thing
        description: "Does NOT do the forbidden thing"
        weight: 20
        check: anti_pattern
      - id: tests_pass
        description: "All tests pass"
        weight: 20
        check: bash_execution
        command: "pytest -q"
    """
).strip()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A fake repo with one lesson (9.9) and a matching learner workspace."""
    repo = tmp_path / "repo"
    lesson = repo / "lessons" / "module-9-fake" / "9.9-fake-lesson"
    lesson.mkdir(parents=True)
    (lesson / "rubric.yaml").write_text(RUBRIC_YAML, encoding="utf-8")

    work = tmp_path / "work"
    chapter_work = work / "9.9"
    chapter_work.mkdir(parents=True)
    (chapter_work / "solution.py").write_text("print('hello')\n", encoding="utf-8")
    # Excluded: prior verifier output and a build cache.
    (chapter_work / "results").mkdir()
    (chapter_work / "results" / "2026-01-01.md").write_text("old report\n", encoding="utf-8")
    (chapter_work / "__pycache__").mkdir()
    (chapter_work / "__pycache__" / "solution.cpython-313.pyc").write_bytes(b"\x00\x01")

    monkeypatch.setenv("LEARN_CLAUDE_REPO", str(repo))
    monkeypatch.setenv("LEARN_CLAUDE_WORK_DIR", str(work))
    monkeypatch.delenv("LEARN_CLAUDE_GRADING_TIMEOUT", raising=False)
    return SimpleNamespace(repo=repo, lesson=lesson, work=work, chapter_work=chapter_work)


# --------------------------------------------------------------------------- #
# chapter validation / discovery
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad", ["3", "3.", "abc", "3.1.2", "", "lessons/3.1"])
def test_invalid_chapter_rejected(env, bad):
    with pytest.raises(grading.GradingError) as ei:
        grading.find_lesson_dir(bad)
    assert ei.value.category == "invalid_chapter"
    assert ei.value.retryable is False


def test_find_lesson_dir_does_not_match_sibling_prefix(env):
    # 9.10 must NOT be found when only 9.9 exists (dash guards the prefix)...
    with pytest.raises(grading.GradingError) as ei:
        grading.find_lesson_dir("9.10")
    assert ei.value.category == "rubric_not_found"
    # ...and 9.9 still resolves cleanly.
    assert grading.find_lesson_dir("9.9") == env.lesson


# --------------------------------------------------------------------------- #
# load_rubric
# --------------------------------------------------------------------------- #


def test_load_rubric_ok(env):
    rubric = grading.load_rubric("9.9")
    assert rubric["chapter"] == "9.9"
    assert [c["id"] for c in rubric["criteria"]] == [
        "does_the_thing",
        "no_forbidden_thing",
        "tests_pass",
    ]
    assert rubric["rubric_path"].endswith("rubric.yaml")


def test_load_rubric_not_found(env):
    (env.lesson / "rubric.yaml").unlink()
    with pytest.raises(grading.GradingError) as ei:
        grading.load_rubric("9.9")
    assert ei.value.category == "rubric_not_found"
    assert ei.value.retryable is False


def test_load_rubric_invalid_yaml(env):
    (env.lesson / "rubric.yaml").write_text("criteria: [unbalanced\n", encoding="utf-8")
    with pytest.raises(grading.GradingError) as ei:
        grading.load_rubric("9.9")
    assert ei.value.category == "rubric_invalid"


def test_load_rubric_missing_criteria_key(env):
    (env.lesson / "rubric.yaml").write_text("chapter: '9.9'\n", encoding="utf-8")
    with pytest.raises(grading.GradingError) as ei:
        grading.load_rubric("9.9")
    assert ei.value.category == "rubric_invalid"


def test_load_rubric_bash_without_command_is_invalid(env):
    bad = textwrap.dedent(
        """
        chapter: "9.9"
        criteria:
          - id: tests_pass
            description: "tests"
            weight: 100
            check: bash_execution
        """
    ).strip()
    (env.lesson / "rubric.yaml").write_text(bad, encoding="utf-8")
    with pytest.raises(grading.GradingError) as ei:
        grading.load_rubric("9.9")
    assert ei.value.category == "rubric_invalid"


# --------------------------------------------------------------------------- #
# load_work
# --------------------------------------------------------------------------- #


def test_load_work_returns_source_excluding_results_and_caches(env):
    work = grading.load_work("9.9")
    paths = {f["path"] for f in work["files"]}
    assert paths == {"solution.py"}
    assert work["files"][0]["content"] == "print('hello')\n"
    # results/ and __pycache__ contents are not surfaced as files.
    assert all("results" not in p and "__pycache__" not in p for p in paths)


def test_load_work_reports_binary_as_skipped(env):
    (env.chapter_work / "blob.bin").write_bytes(b"\xff\xfe\x00\x01\x02")
    work = grading.load_work("9.9")
    assert "blob.bin" not in {f["path"] for f in work["files"]}
    assert any(s["path"] == "blob.bin" and s["reason"] == "binary" for s in work["skipped"])


def test_load_work_reports_oversized_as_skipped(env):
    (env.chapter_work / "big.txt").write_text("x" * 10_000, encoding="utf-8")
    work = grading.load_work("9.9", max_file_bytes=1024)
    assert any(s["path"] == "big.txt" and s["reason"] == "too_large" for s in work["skipped"])


def test_load_work_missing_dir(env):
    # 9.9 has a workspace; 1.1 is a valid chapter id with no workspace set up.
    with pytest.raises(grading.GradingError) as ei:
        grading.load_work("1.1")
    assert ei.value.category == "work_dir_missing"
    assert ei.value.retryable is False
    assert "/exercise 1.1" in (ei.value.hint or "")


# --------------------------------------------------------------------------- #
# run_bash_check
# --------------------------------------------------------------------------- #


def _fake_run(returncode=0, stdout="", stderr=""):
    def _run(command, shell, cwd, capture_output, text, timeout):
        _run.calls.append(SimpleNamespace(command=command, cwd=cwd, timeout=timeout))
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    _run.calls = []
    return _run


def test_run_bash_check_pass(env, monkeypatch):
    fake = _fake_run(returncode=0, stdout="2 passed\n")
    monkeypatch.setattr(subprocess, "run", fake)
    out = grading.run_bash_check("9.9", "pytest -q")
    assert out["passed"] is True
    assert out["exit_code"] == 0
    assert out["stdout"] == "2 passed\n"
    # Ran inside the chapter's work dir.
    assert fake.calls[0].cwd == str(env.chapter_work)
    assert fake.calls[0].command == "pytest -q"


def test_run_bash_check_fail_is_a_result_not_an_error(env, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(returncode=1, stderr="1 failed\n"))
    out = grading.run_bash_check("9.9", "pytest -q")
    assert out["passed"] is False
    assert out["exit_code"] == 1
    assert "error" not in out


def test_run_bash_check_timeout_is_retryable(env, monkeypatch):
    def _boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="pytest -q", timeout=120)

    monkeypatch.setattr(subprocess, "run", _boom)
    with pytest.raises(grading.GradingError) as ei:
        grading.run_bash_check("9.9", "pytest -q")
    assert ei.value.category == "command_timeout"
    assert ei.value.retryable is True


def test_run_bash_check_launch_failure(env, monkeypatch):
    def _boom(*a, **k):
        raise OSError("no shell")

    monkeypatch.setattr(subprocess, "run", _boom)
    with pytest.raises(grading.GradingError) as ei:
        grading.run_bash_check("9.9", "nope")
    assert ei.value.category == "command_failed"
    assert ei.value.retryable is False


def test_run_bash_check_empty_command(env):
    with pytest.raises(grading.GradingError) as ei:
        grading.run_bash_check("9.9", "   ")
    assert ei.value.category == "invalid_command"


def test_run_bash_check_missing_work_dir(env):
    with pytest.raises(grading.GradingError) as ei:
        grading.run_bash_check("1.1", "pytest -q")
    assert ei.value.category == "work_dir_missing"


def test_run_bash_check_output_truncated(env, monkeypatch):
    huge = "y" * (grading.MAX_OUTPUT_CHARS + 500)
    monkeypatch.setattr(subprocess, "run", _fake_run(returncode=0, stdout=huge))
    out = grading.run_bash_check("9.9", "echo big")
    assert len(out["stdout"]) < len(huge)
    assert "truncated" in out["stdout"]


# --------------------------------------------------------------------------- #
# grade
# --------------------------------------------------------------------------- #


def test_grade_runs_bash_and_defers_review(env, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(returncode=0, stdout="ok\n"))
    report = grading.grade("9.9")
    by_id = {r["id"]: r for r in report["results"]}

    assert by_id["does_the_thing"]["status"] == "needs_review"
    assert by_id["no_forbidden_thing"]["status"] == "needs_review"
    assert by_id["tests_pass"]["status"] == "pass"
    assert by_id["tests_pass"]["result"]["exit_code"] == 0

    # Rubric and work are bundled in.
    assert report["rubric"]["chapter"] == "9.9"
    assert {f["path"] for f in report["work"]["files"]} == {"solution.py"}


def test_grade_records_bash_error_per_criterion(env, monkeypatch):
    def _boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="pytest -q", timeout=120)

    monkeypatch.setattr(subprocess, "run", _boom)
    report = grading.grade("9.9")
    bash = next(r for r in report["results"] if r["id"] == "tests_pass")
    assert bash["status"] == "error"
    assert bash["error"]["category"] == "command_timeout"
    assert bash["error"]["retryable"] is True
    # Other criteria still evaluated.
    assert any(r["status"] == "needs_review" for r in report["results"])


def test_grade_propagates_missing_workspace(env):
    # Rubric exists (9.9) but the workspace is gone — grade must surface that.
    import shutil

    shutil.rmtree(env.chapter_work)
    with pytest.raises(grading.GradingError) as ei:
        grading.grade("9.9")
    assert ei.value.category == "work_dir_missing"


# --------------------------------------------------------------------------- #
# error envelope
# --------------------------------------------------------------------------- #


def test_error_envelope_shape():
    err = grading.GradingError("work_dir_missing", "nope", retryable=False, hint="do x")
    env_dict = err.to_envelope()
    assert env_dict == {
        "error": {
            "category": "work_dir_missing",
            "message": "nope",
            "retryable": False,
            "hint": "do x",
        }
    }


def test_error_envelope_omits_absent_hint():
    err = grading.GradingError("rubric_invalid", "bad", retryable=False)
    assert "hint" not in err.to_envelope()["error"]
