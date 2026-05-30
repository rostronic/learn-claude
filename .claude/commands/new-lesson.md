Scaffold a new Learn Claude lesson and guide the author through filling it in.

The user invoked `/new-lesson $ARGUMENTS`. Treat `$ARGUMENTS` as a chapter id in dotted form (`module.lesson`, e.g. `2.1`) — the learning-path course id, not an exam's numbering. If empty, ask which chapter they want to build and offer `docs/curriculum-map.md` for the list of planned chapters. Stop until you have one.

> **This is an authoring/infra command (Phase 5), not a learner command.** It builds the skeleton of a chapter the way a contributor would, then walks the author through filling it with real content. It is a **guided scaffold, not a silent generator**: you create structurally-valid placeholder files and then *teach the author what to put where*, per the authoring rules. **Do not invent lesson prose, code, or exam claims** — that's the author's job (and a separate content task). Read the rules before you write a single file: `.claude/rules/lesson-authoring.md` and `.claude/rules/rubric-authoring.md` load automatically when you touch matching files, but read them now so your scaffold matches them.

## Step 1 — Look up the chapter and refuse to clobber

1. **Find the title and module.** Read `docs/curriculum-map.md` and locate the row for `$ARGUMENTS`. Grab its **title** and the **module** it lives under (e.g. `2.1` → "Built-in tools (Read, Write, Edit, Bash, Grep, Glob)" under "Module 2 — Tools"). If the chapter isn't in the map at all, stop and tell the author it's not a planned chapter — the curriculum map is the source of truth for what exists.
2. **Check it isn't already built.** If the curriculum-map row says **built**, *or* `Glob` for `lessons/**/$ARGUMENTS-*/lesson.md` finds an existing lesson, **stop**: tell the author the chapter is already built and point them at `/study $ARGUMENTS` (to read it) or the `lesson-auditor` (to QA it). Never overwrite an existing lesson.
3. **Find the exam mapping.** Read `docs/exam-mapping.md`. Find the `coverage:` entry whose `lesson_chapter` equals `$ARGUMENTS`. Record its `task_statement`, `domain`, and `exam` (currently always `CCAF`). If there is **no** entry, the lesson is **unmapped** ("just learn Claude") — it gets **no** "Exam coverage" footer and **no** "Exam focus" section. Most planned chapters are mapped; an unmapped one is the exception.

## Step 2 — Settle the naming, then confirm with the author

Derive these and **show them to the author for a quick confirm before writing anything** (the slug especially — it's load-bearing and renaming later is painful):

- **`slug`** — kebab-case, derived from the title (e.g. "Built-in tools (Read, Write, Edit, Bash, Grep, Glob)" → `built-in-tools`). Keep it short and topical; drop parentheticals. If the exam-mapping entry already carries a `lesson_slug`, use that verbatim.
- **module directory** — `module-<N>-<kebab>` matching the existing dirs (e.g. `module-2-tools`). Check `lessons/` for the convention; create the module dir if it doesn't exist yet.
- **module-snake** — the lesson directory's Python module name for the starter, snake_case from the slug (e.g. `built_in_tools`). Used for the starter `.py` filename and its test.
- **`sequence`** — the lesson's **global position in the learning path**. Count chapters in `docs/curriculum-map.md` order up to and including this one. State the number you derived so the author can correct it.

Confirm slug + sequence with the author in one short turn, then proceed. The lesson directory is `lessons/<module-dir>/$ARGUMENTS-<slug>/`.

## Step 3 — Write the skeleton

Create the directory and these files with the **Write** tool. Fill the `<ANGLE-BRACKET>` fields from Steps 1–2; leave the `TODO(author):` markers for the human (or a follow-up content task). The result must be **structurally valid the moment it's written** — frontmatter parses, the six sections are present and ordered, the rubric weights sum to 100 with an `anti_pattern` and a `bash_execution` pytest criterion, and the starter compiles (`python -m py_compile`). It just won't have real content yet.

### `lesson.md`

Include the "## Exam coverage" footer and "## Exam focus" section **only if the lesson is mapped** (Step 1.3). Omit both for unmapped lessons.

````markdown
---
chapter: "$ARGUMENTS"
slug: "<slug>"
title: "<title>"
module: "<module-dir>"
sequence: <sequence>
references:
  # TODO(author): list the OFFICIAL Anthropic/Claude docs this lesson teaches from.
  # ≥1 entry, every url on docs.claude.com / code.claude.com / platform.claude.com.
  # No exam-guide entries here (exam alignment lives in docs/exam-mapping.md), no third-party domains.
  - title: "<official doc title>"
    url: "https://docs.claude.com/"   # TODO(author): replace with the exact page you cite
    type: official_docs
    covers: "<what this doc backs in the lesson>"
---

# <title>

## Overview

TODO(author): What this is, where it fits in the broader Claude toolkit, and why it matters. A few short orienting paragraphs. State the task statement plainly. (See lesson-authoring rules — section is a 5–10 min read, no "in this lesson we will…" preamble.)

## How it works

TODO(author): The mechanism, taught in depth — this is the core of the lesson. Explain the model/SDK behavior accurately, with **inline citations** to the `references:` docs where you make a claim. Include runnable `anthropic`-SDK Python that illustrates the mechanism (real API shapes: `client.messages.create(...)`, `response.stop_reason`, the `{"name":…, "description":…, "input_schema":{…}}` tool shape; model id `claude-sonnet-4-6` or `claude-opus-4-8`).

## Worked example

TODO(author): A complete, runnable end-to-end example that puts the mechanism to work. Real code, not pseudocode. Walk the reader through it.

## Anti-patterns & pitfalls

TODO(author): The wrong approaches the exam tempts you with, and *why* each fails. If the lesson is exam-mapped, quote the task statement's "Avoiding anti-patterns such as…" list from the exam guide. Be definitive — the "Anthropic way" rule applies; name the prescribed approach and call the alternatives wrong.

## Exam focus

TODO(author): (Mapped lessons only — delete this whole section if unmapped.) Short: which of the exam's scenarios/areas this topic powers and what distractors it reliably offers.

## References & further reading

TODO(author): Render the frontmatter `references:` as a readable list (title + link + what it covers), plus any prose pointers to adjacent official docs.

## Exam coverage

TODO(author): (Mapped lessons only — delete this whole footer if unmapped. Must agree with docs/exam-mapping.md.)

- **<exam>** — Domain <domain> (<domain name>), Task Statement <task_statement>.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
````

### `exercise.md`

````markdown
# <title> — exercise

## What you're building

TODO(author): One paragraph — the concrete thing the learner implements, tying back to the lesson's mechanism.

## Function signature / spec

TODO(author): The exact contract the learner codes to (function name, args, return), matching the starter skeleton.

## Requirements

You must:

1. TODO(author): the positive requirements, each one a rubric `code_review` criterion.
2. TODO(author): …
3. **Pass every test in `test_<module-snake>.py`.**

You must NOT:

4. TODO(author): the forbidden pattern(s) — each maps to a rubric `anti_pattern` criterion. Phrase as "do NOT …". These are graded directly; they fail the rubric whether or not the tests pass.

## How to run it

```bash
cd ~/learn-claude-work/$ARGUMENTS
pip install -r requirements.txt
pytest -v
```

The tests mock the Anthropic client — no `ANTHROPIC_API_KEY` needed, no credits burned.

When you're ready (or stuck), run `/verify $ARGUMENTS` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- TODO(author): the same official docs as the lesson's `references:`.
````

### `rubric.yaml`

The contract the `verifier` grades against. Weights **must sum to exactly 100**; there **must** be ≥1 `anti_pattern` criterion and a `bash_execution` pytest criterion. This template already satisfies both — the author refines the descriptions and weights, keeping the sum at 100.

```yaml
chapter: "$ARGUMENTS"
criteria:
  - id: <snake_case_id_1>
    description: "TODO(author): a specific, checkable assertion about the learner's code (see rubric-authoring 'Specificity')."
    weight: 30
    check: code_review
  - id: <snake_case_id_2>
    description: "TODO(author): a second specific code_review assertion."
    weight: 25
    check: code_review
  - id: <snake_case_anti_pattern_id>
    description: "TODO(author): a forbidden pattern the learner must NOT use (phrase as what they must NOT do)."
    weight: 25
    check: anti_pattern
  - id: tests_pass
    description: "All tests in test_<module-snake>.py pass"
    weight: 20
    check: bash_execution
    command: "pytest test_<module-snake>.py -v"
```

### `starter/<module-snake>.py`

```python
"""Starter skeleton for Learn Claude chapter $ARGUMENTS — <title>.

Implement the function below. See exercise.md for the full spec.
"""


def solve(*args, **kwargs):
    """TODO(author): real signature + docstring matching exercise.md."""
    raise NotImplementedError("Implement solve — see exercise.md")
```

### `starter/test_<module-snake>.py`

```python
"""Tests for chapter $ARGUMENTS. These mock the Anthropic client — no API key needed.

TODO(author): replace the skipped placeholder with real tests that exercise the
spec in exercise.md. Mock anthropic.Anthropic() (see chapter 3.1's test file for
the SimpleNamespace/MagicMock pattern) so grading never calls the live API.
"""

import pytest

from <module-snake> import solve


@pytest.mark.skip(reason="TODO(author): write real tests for this exercise")
def test_placeholder():
    assert callable(solve)
```

### `starter/requirements.txt`

```
anthropic>=0.40.0
pytest>=8.0.0
```

After writing, run `python -m py_compile` on the two starter `.py` files to confirm the skeleton compiles, and report the result.

## Step 4 — Walk the author through filling it in

Don't dump the files back. **Coach the author**, section by section, in the order they'll write:

1. **`references:` first.** The lesson is built *from* official docs — have them pick the exact `docs.claude.com` / `code.claude.com` / `platform.claude.com` pages before writing prose, because every claim must cite one. Remind them: no exam-guide URLs here, no third-party.
2. **The six sections**, in order, each a focused 5–10 min read; positive teaching first, anti-patterns as one section. If mapped, the "Anti-patterns" section should lift the task statement's "Avoiding anti-patterns such as…" list, and the "Exam focus" + "Exam coverage" footer must match `docs/exam-mapping.md`.
3. **The exercise + rubric together** — every "You must" becomes a `code_review` criterion, every "You must NOT" an `anti_pattern`; keep weights summing to 100 and the `tests_pass` `bash_execution` criterion. Point them at the runnability rule (`pip install -r requirements.txt && pytest`, tests mock the API).
4. **The starter** — real signature, real mocked tests. Reference `lessons/module-3-agentic-core/3.1-agentic-loops/starter/` as the worked template for the test-mocking pattern.

Be concrete about *which file and section* each piece goes in; let the author write the actual content.

## Step 5 — Tell them how to finish

End by spelling out the closeout steps (don't do them silently — they're the author's to complete once the content is real):

1. **Run the `lesson-auditor` on the chapter** (`subagent_type: lesson-auditor`, input `$ARGUMENTS`) — it checks accuracy against the cited docs and compliance with the authoring rules, and will catch a half-filled scaffold. Iterate until it returns **PASS**.
2. **Flip the status to built in both maps** once the auditor passes: update the chapter's row in `docs/curriculum-map.md` (and the "Status:" / totals line) and its `coverage:` entry + table row in `docs/exam-mapping.md` from `planned` to `built`. Then optionally run the `curriculum-auditor` to confirm the map stayed consistent.
3. **Seed practice questions** with `/new-question $ARGUMENTS` so `/practice` has something to draw.

## Tone

You're a build assistant for a contributor, not a content generator. Produce a clean, valid skeleton fast, then get out of the way and coach — the human owns the words, the code, and every exam claim. Never fabricate citations or invent what a doc says.
