# Learn Claude — editorial constitution

This file governs every lesson, exercise, and rubric in this repo. If you're authoring content here (whether you're a human contributor or Claude Code), these rules are load-bearing — exam validity depends on them.

## What this project is

Learn Claude is a study platform for the **Claude Certified Architect — Foundations (CCA-F)** exam. Our audience is working engineers preparing for that specific cert. Every piece of content here exists to help someone pass that exam.

## Scope authority vs. teaching sources

Two kinds of source, two distinct jobs. Don't conflate them.

- **Scope authority — the CCA-F Exam Guide** (PDF linked from the README). It is the *only* authority on **what's testable**: the task-statement spine, the anti-patterns candidates are expected to avoid, and which scenarios matter. Every lesson and every rubric criterion must trace back to a specific task statement in the guide, and the lesson must cite it by ID (`1.1`, `2.3`, etc.) and exact title. If you're unsure what's in scope, **read the guide** — don't invent, don't paraphrase from memory, don't pull a topic in just because it's interesting.
- **Teaching reference — the official Anthropic / Claude docs** (`docs.claude.com`, `code.claude.com`, `platform.claude.com`). These are the canonical reference for **how the thing actually works**. Use them to teach with depth and accuracy: cite them inline where you make a claim, and list them in the lesson's `references:` frontmatter so the reader can go deeper and so tooling can surface and lint them.

The exam guide decides *what* we teach; the official docs help us teach it *well*. **Third-party blogs, videos, and tutorials remain off-limits** — they dilute the source of truth and date badly. If a claim isn't supported by the exam guide (for scope) or an official doc (for mechanics), it doesn't go in a lesson.

## Tone

Lessons are **readable learning resources**, not cram sheets. A learner should be able to sit down, read a lesson end-to-end, and actually understand the topic — while still walking away exam-ready.

- **Readable, not padded.** Teach the topic properly, with enough context and worked detail to genuinely learn it. Brief orientation ("what this is, where it fits") is welcome. What's not welcome is filler — no "in this lesson we will…", no marketing, no closing recap that repeats what you just said.
- **Anti-patterns are a required section, not the spine.** Every lesson must call out the wrong approaches the exam tempts you with (and *why* they fail), but they're one part of a lesson that teaches the topic positively — not the organizing principle. (See the section structure in `.claude/rules/lesson-authoring.md`.)
- **Treat the reader as a working engineer.** They know what a function is and have used an API. Skip the fundamentals; spend the words on what's actually specific to Claude and to the exam.
- **Cite as you teach.** Back claims with inline links to the official docs (see "Scope authority vs. teaching sources"). A reader should be able to follow any assertion to its source.

## The "Anthropic way" rule

When the exam guide gives a definitive answer on a tradeoff, **state it explicitly and call alternatives wrong.** The CCA-F is opinionated — it rewards candidates who know Anthropic's prescribed approach, not candidates who present both sides.

Examples of opinions you must take:
- **Programmatic enforcement (hooks, prerequisite gates) over prompt instructions** for any business rule requiring deterministic compliance — see Task Statements 1.4 and 1.5.
- **`stop_reason` is the only valid loop-termination signal** — parsing text or counting iterations is wrong (Task Statement 1.1).
- **Tool descriptions, not few-shot examples, are the first fix for tool-selection failures** (Task Statement 2.1, sample Q2).
- **Independent review instances beat self-review** (Task Statement 4.6).

When a lesson covers ground like this, say so directly. "Both approaches have merit" is the wrong tone for this exam.

## The runnability rule

Every exercise must run with:

```bash
pip install -r requirements.txt && pytest
```

No exceptions, no out-of-band setup, no "first install Docker." If the exercise needs the Anthropic API, the tests must mock it — we don't burn the user's API credits to grade their homework. The verifier (Phase 2+) will actually execute these.

## The anti-pattern criterion rule

Every `rubric.yaml` must include **at least one criterion with `check: anti_pattern`** — something the user must NOT do. This is non-negotiable. The exam rewards knowing what's wrong as much as knowing what's right; our rubrics must reflect that.

## Path-specific conventions

Topic-specific rules live in [.claude/rules/](.claude/rules/) and load automatically when you edit matching files:

- [.claude/rules/lesson-authoring.md](.claude/rules/lesson-authoring.md) — loads on any `lessons/**/*.md` edit
- [.claude/rules/rubric-authoring.md](.claude/rules/rubric-authoring.md) — loads on any `lessons/**/rubric.yaml` edit

If you find yourself wanting a global rule that only applies to one file type, put it in `.claude/rules/` with path scoping instead of adding it here.
