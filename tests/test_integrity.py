"""Cross-cutting integrity invariants surfaced by iterative deep-validation.

Encodes the design-exercise convention: a chapter either ships a coding `starter/`
(with tests + a bash_execution rubric criterion) OR is a design exercise (no
`starter/`, and therefore no bash_execution criterion). The scenario capstones
(7.7–7.10) are design exercises by intent.
"""

import pathlib
import re

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
LESSONS = sorted(REPO.glob("lessons/module-*/*/lesson.md"))
CHAPTERS = [(p, re.search(r"/(\d+\.\d+)-", str(p)).group(1)) for p in LESSONS]
IDS = [c for _, c in CHAPTERS]


def _fm(p):
    return yaml.safe_load(p.read_text(encoding="utf-8").split("---")[1])


def test_sequence_unique_and_contiguous():
    seqs = [_fm(p)["sequence"] for p in LESSONS]
    assert len(set(seqs)) == len(seqs), "duplicate sequence numbers across chapters"
    assert sorted(seqs) == list(range(1, len(seqs) + 1)), (
        f"sequence not contiguous 1..{len(seqs)}: {sorted(seqs)}"
    )


def test_slugs_unique():
    slugs = [_fm(p)["slug"] for p in LESSONS]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    assert not dupes, f"duplicate slugs: {dupes}"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_exercise_md_present(path, chapter):
    assert (path.parent / "exercise.md").exists(), f"{chapter}: missing exercise.md"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_rubric_criterion_ids_unique(path, chapter):
    rb = yaml.safe_load((path.parent / "rubric.yaml").read_text(encoding="utf-8"))
    ids = [c["id"] for c in rb["criteria"]]
    assert len(set(ids)) == len(ids), f"{chapter}: duplicate criterion id"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_starter_convention(path, chapter):
    """Coding exercise => starter with tests + a runnable bash criterion;
    design exercise => no starter AND no bash_execution criterion."""
    starter = path.parent / "starter"
    rb = yaml.safe_load((path.parent / "rubric.yaml").read_text(encoding="utf-8"))
    bash = [c for c in rb["criteria"] if c["check"] == "bash_execution"]
    if starter.is_dir():
        assert list(starter.glob("**/test_*.py")), f"{chapter}: starter/ has no test_*.py"
        assert (starter / "requirements.txt").exists(), f"{chapter}: starter/ has no requirements.txt"
        for c in bash:
            m = re.search(r"(test_\w+\.py)", c.get("command", ""))
            if m:
                assert (starter / m.group(1)).exists(), (
                    f"{chapter}: bash criterion '{c['id']}' runs {m.group(1)} which is missing"
                )
    else:
        assert not bash, (
            f"{chapter}: a design exercise (no starter/) must not have a bash_execution criterion"
        )


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_exercise_workdir_path_matches_chapter(path, chapter):
    text = (path.parent / "exercise.md").read_text(encoding="utf-8")
    for ref in re.findall(r"learn-claude-work/(\d+\.\d+)", text):
        assert ref == chapter, f"{chapter}: exercise.md references work dir {ref}"
    for ref in re.findall(r"/verify (\d+\.\d+)", text):
        assert ref == chapter, f"{chapter}: exercise.md says /verify {ref}"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_lesson_internal_links_resolve(path, chapter):
    for link in re.findall(r"\]\((\.\.?/[^)\s]+)\)", path.read_text(encoding="utf-8")):
        target = (path.parent / link.split("#")[0]).resolve()
        assert target.exists(), f"{chapter}: broken internal link {link}"


def test_exam_mapping_slugs_match_dirs():
    fm = yaml.safe_load((REPO / "docs/exam-mapping.md").read_text(encoding="utf-8").split("---")[1])
    by_chapter = {c: re.search(r"/(\d+\.\d+)-(.+)/lesson\.md", str(p)).group(2)
                  for p in LESSONS
                  for c in [re.search(r"/(\d+\.\d+)-", str(p)).group(1)]}
    for entry in fm["exams"]["CCAF"]["coverage"]:
        slug = entry.get("lesson_slug")
        ch = entry["lesson_chapter"]
        if slug and ch in by_chapter:
            assert by_chapter[ch] == slug, (
                f"exam-mapping {ch} lesson_slug '{slug}' != dir slug '{by_chapter[ch]}'"
            )


def test_exam_domain_weights_sum_100():
    ex = yaml.safe_load((REPO / "exams/CCAF/exam.yaml").read_text(encoding="utf-8"))
    assert sum(ex["domain_weights"].values()) == 100
