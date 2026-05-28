# Learn Claude — editorial constitution

This file governs every lesson, exercise, and rubric in this repo. If you're authoring content here (whether you're a human contributor or Claude Code), these rules are load-bearing — exam validity depends on them.

## What this project is

Learn Claude is a study platform for the **Claude Certified Architect — Foundations (CCA-F)** exam. Our audience is working engineers preparing for that specific cert. Every piece of content here exists to help someone pass that exam.

## The source-of-truth rule

The official **CCA-F Exam Guide** (PDF linked from the README) is the *only* source of truth for what we teach. Every lesson and every rubric criterion must trace back to a specific task statement in the guide — and the lesson must cite it by ID (`1.1`, `2.3`, etc.) and exact title in the opening line.

If you're unsure what the guide says about a topic, **read the guide.** Don't invent. Don't paraphrase from memory. Don't pull in adjacent material from Anthropic blog posts or third-party tutorials unless it directly supports a task statement that's already in scope.

## Tone

- **Concise.** Lessons cap at ~800 words. Depth comes from the exercise, not the prose.
- **Anti-pattern first.** Show the wrong way the exam will test, then the right way. Engineers learn faster from "don't do X because Y" than from a green-field tutorial.
- **No fluff.** No motivational openers, no "in this lesson we will…", no closing recaps. Get in, teach, get out.
- **Treat the reader as a working engineer.** They know what a function is. They've used an API. Skip the basics and respect their time.

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
