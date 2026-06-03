"""Structural validation of every lesson — frontmatter, references, rubric.

Platform test suite (infrastructure, not coursework). Runs against the repo's
authoring conventions in .claude/rules/lesson-authoring.md + rubric-authoring.md.
"""

import pathlib
import re

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
LESSONS = sorted(REPO.glob("lessons/module-*/*/lesson.md"))
CHAPTERS = [(p, re.search(r"/(\d+\.\d+)-", str(p)).group(1)) for p in LESSONS]
IDS = [c for _, c in CHAPTERS]
OFFICIAL = re.compile(r"^https://(docs|code|platform)\.claude\.com/")


def _frontmatter(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


def test_there_are_lessons():
    assert LESSONS, "no lessons found under lessons/module-*/*/"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_frontmatter_fields(path, chapter):
    fm = _frontmatter(path)
    for key in ("chapter", "slug", "title", "module", "sequence"):
        assert key in fm, f"{chapter}: missing frontmatter key '{key}'"
    assert fm["chapter"] == chapter, f"{chapter}: frontmatter chapter={fm['chapter']}"
    assert path.parent.name == f"{fm['chapter']}-{fm['slug']}", (
        f"{chapter}: dir '{path.parent.name}' != '{fm['chapter']}-{fm['slug']}'"
    )
    assert fm["module"] == path.parent.parent.name, f"{chapter}: module mismatch"
    assert isinstance(fm["sequence"], int), f"{chapter}: sequence must be an int"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_references_are_official(path, chapter):
    refs = _frontmatter(path).get("references", [])
    assert refs, f"{chapter}: no references"
    for r in refs:
        assert r.get("type") == "official_docs", f"{chapter}: ref type != official_docs: {r}"
        assert OFFICIAL.match(r["url"]), f"{chapter}: non-official reference URL: {r['url']}"


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_h1_is_title(path, chapter):
    body = path.read_text(encoding="utf-8").split("---", 2)[2]
    h1 = next((l for l in body.splitlines() if l.startswith("# ")), None)
    assert h1, f"{chapter}: no H1 heading"
    assert h1.lstrip("# ").strip() == _frontmatter(path)["title"], (
        f"{chapter}: H1 '{h1}' != title '{_frontmatter(path)['title']}'"
    )


@pytest.mark.parametrize("path,chapter", CHAPTERS, ids=IDS)
def test_rubric(path, chapter):
    rp = path.parent / "rubric.yaml"
    assert rp.exists(), f"{chapter}: missing rubric.yaml"
    rb = yaml.safe_load(rp.read_text(encoding="utf-8"))
    assert rb.get("chapter") == chapter, f"{chapter}: rubric chapter={rb.get('chapter')}"
    crit = rb.get("criteria")
    assert isinstance(crit, list) and crit, f"{chapter}: rubric has no criteria"
    assert sum(c["weight"] for c in crit) == 100, f"{chapter}: weights sum != 100"
    assert any(c["check"] == "anti_pattern" for c in crit), f"{chapter}: no anti_pattern criterion"
    for c in crit:
        assert c["check"] in ("code_review", "anti_pattern", "bash_execution"), (
            f"{chapter}: bad check '{c['check']}'"
        )
        if c["check"] == "bash_execution":
            assert c.get("command"), f"{chapter}: bash_execution criterion '{c['id']}' has no command"
