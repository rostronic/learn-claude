"""Consistency of the curriculum map and the exam-mapping overlay against disk.

Catches the parallel-merge drift class of bug: a chapter marked built in one
file but not on disk (or in the other map), or exam coverage gaps.
"""

import pathlib
import re

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]


def _disk_chapters():
    return {re.search(r"/(\d+\.\d+)-", str(p)).group(1)
            for p in REPO.glob("lessons/module-*/*/lesson.md")}


def _cm_built():
    text = (REPO / "docs/curriculum-map.md").read_text(encoding="utf-8")
    return set(re.findall(r"^\|\s*(\d+\.\d+)\s*\|.*\|\s*\*\*built\*\*\s*\|", text, re.M))


def _exam_coverage():
    fm = yaml.safe_load((REPO / "docs/exam-mapping.md").read_text(encoding="utf-8").split("---")[1])
    return fm["exams"]["CCAF"]["coverage"]


def test_curriculum_map_built_matches_disk():
    cm, disk = _cm_built(), _disk_chapters()
    assert cm == disk, f"curriculum-map built {sorted(cm)} != disk {sorted(disk)}"


def test_exam_mapping_covers_all_ccaf_items_once():
    cov = _exam_coverage()
    ts = [c["task_statement"] for c in cov]
    assert len(ts) == 36, f"expected 36 CCAF items (30 task statements + 6 scenarios), got {len(ts)}"
    assert len(ts) == len(set(ts)), "duplicate task_statement in exam coverage"
    chapters = [c["lesson_chapter"] for c in cov]
    assert len(chapters) == len(set(chapters)), "two task statements map to the same chapter"


def test_exam_mapping_built_entries_exist_on_disk():
    disk = _disk_chapters()
    for c in _exam_coverage():
        if c["status"] == "built":
            assert c["lesson_chapter"] in disk, (
                f"exam-mapping says '{c['task_statement']}' -> {c['lesson_chapter']} built, "
                f"but no lesson on disk"
            )


def test_built_status_consistent_between_maps():
    cm = _cm_built()
    em_built = {c["lesson_chapter"] for c in _exam_coverage() if c["status"] == "built"}
    # every exam-mapping-built chapter must be built in the curriculum map too
    # (the reverse can differ: 0.1 is built but unmapped)
    assert em_built <= cm, f"built in exam-mapping but not curriculum-map: {sorted(em_built - cm)}"


def test_mapped_chapters_have_exam_coverage_footer():
    mapped = {c["lesson_chapter"] for c in _exam_coverage()}
    for p in REPO.glob("lessons/module-*/*/lesson.md"):
        ch = re.search(r"/(\d+\.\d+)-", str(p)).group(1)
        if ch in mapped:
            assert "## Exam coverage" in p.read_text(encoding="utf-8"), (
                f"{ch}: mapped to an exam but has no '## Exam coverage' footer"
            )
