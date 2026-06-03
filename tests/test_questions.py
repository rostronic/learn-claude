"""Schema validation for assessment questions (mock-exam bank + per-lesson practice)."""

import pathlib

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]


def _load(path):
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    return d.get("questions", d) if isinstance(d, dict) else d


def _bank_files():
    return sorted(REPO.glob("exams/*/questions/*.yaml"))


def _practice_files():
    return sorted(REPO.glob("lessons/module-*/*/practice.yaml"))


def test_questions_exist():
    assert _bank_files(), "no mock-exam bank question files"
    assert _practice_files(), "no per-lesson practice files"


def test_question_schema():
    seen_ids = set()
    for path in _bank_files() + _practice_files():
        for q in _load(path) or []:
            qid = q.get("id")
            assert qid, f"{path.name}: question with no id"
            assert qid not in seen_ids, f"duplicate question id: {qid}"
            seen_ids.add(qid)
            assert q.get("stem"), f"{qid}: no stem"
            assert set((q.get("options") or {}).keys()) == set("ABCD"), f"{qid}: options must be A-D"
            assert q.get("correct") in ("A", "B", "C", "D"), f"{qid}: correct must be A-D"
            assert q.get("explanation"), f"{qid}: no explanation"


def test_bank_questions_carry_exam_metadata():
    for path in _bank_files():
        for q in _load(path) or []:
            qid = q.get("id")
            assert q.get("exam"), f"{qid}: bank question missing 'exam'"
            assert q.get("domain") is not None, f"{qid}: bank question missing 'domain'"
            assert q.get("scenario") is not None or q.get("task_statement"), (
                f"{qid}: bank question needs a scenario or task_statement"
            )


def test_all_six_ccaf_scenarios_populated():
    """A 4-of-6 mock-exam draw needs every scenario to have questions."""
    scenarios = set()
    for path in REPO.glob("exams/CCAF/questions/*.yaml"):
        for q in _load(path) or []:
            if q.get("scenario"):
                scenarios.add(q["scenario"])
    assert scenarios >= set(range(1, 7)), f"scenarios populated: {sorted(scenarios)} (need 1-6)"
