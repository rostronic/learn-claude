---
paths: ["exams/**/*.yaml", "lessons/**/practice.yaml"]
---

# Question authoring rules

These rules load when you edit a mock-exam pool (`exams/**/*.yaml`) or a per-lesson `practice.yaml`. They build on the editorial constitution in the root [CLAUDE.md](../../CLAUDE.md). Assessment questions feed the read-only `examiner` subagent, which powers `/practice` and `/mock-exam`.

## Two homes, one schema

- **Mock-exam bank** — `exams/<CODE>/questions/*.yaml`. Each file is a list of questions for one scenario (or domain). Carries full metadata. `exams/<CODE>/exam.yaml` holds the assembly config (scoring, scenario/question counts, domain weights) and must trace to the exam guide — don't invent weights or thresholds.
- **Per-lesson practice** — `lessons/**/<chapter>-*/practice.yaml`: a top-level `chapter: "<M.L>"` plus a `questions:` list. Topic drills for that chapter; `exam`/`domain`/`task_statement`/`scenario` are optional here (the chapter's exam mapping already lives in `docs/exam-mapping.md`).

```yaml
- id: "ccaf-d1-1.4-001"          # stable, unique; convention: <exam>-d<domain>-<task>-NNN
  stem: >-
    A production-context multiple-choice question…
  options:
    A: "…"
    B: "…"
    C: "…"
    D: "…"
  correct: "A"                    # exactly one of A/B/C/D
  explanation: >-
    Why A is right, AND why B, C, and D each fail.
  exam: "CCAF"                    # bank: required; practice: optional
  domain: 1                       # the domain this question SCORES under (drives weighting)
  task_statement: "1.4 …"         # the task statement it tests
  scenario: 1                     # 1–6 for scenario questions; omit for topic-only practice
```

## Sourcing (scope authority)

- **Every question traces to the exam guide** — its in-scope topics and a specific task statement (and, for bank questions, a scenario). The exam guide is the only authority on what's testable; if you're unsure it's in scope, read the guide. No third-party sources, no out-of-scope trivia.
- **The official sample questions are verbatim anchors.** The questions reproduced from the guide's "Sample Questions" section (currently `ccaf-d1-1.4-001` and `ccaf-d2-2.1-001` in `scenario-1-customer-support.yaml`) are copied exactly — stem, options, `correct`, explanation — and tagged `source: "CCA-F exam guide …"`. Do not reword them; they calibrate the rest of the pool.

## Format rules

- **Exactly one correct answer and three distractors.** Four options, A–D.
- **Distractors must be plausible-but-wrong** — the approaches a candidate with partial knowledge would actually pick. On this exam, the best distractors are usually the **anti-patterns the lessons warn about** (prompt-based enforcement where programmatic is required, few-shot where a tool description is the fix, parsing text for loop termination, etc.). The "Anthropic way" rule applies: the correct option is the prescribed approach, not "it depends."
- **The `explanation` must justify the key AND refute each distractor** — one clause per wrong option saying *why* it fails. A reveal that only praises the right answer is incomplete (mirror the official samples).
- **`domain` is the domain the question scores under** — pick the single task statement it most tests; that tag drives `/mock-exam` domain weighting. Tag `scenario` with the production context it's framed in.
- **`id` is stable** — the examiner and (Phase 4) progress tracker key off it; don't renumber a published question.

## Coverage (bank)

Aim for enough questions that `/mock-exam` can assemble a domain-weighted run from **any 4 of the 6 scenarios** — i.e. keep all six scenarios populated, and spread questions across the five domains in roughly their weights (D1 27, D2 18, D3 20, D4 20, D5 15). A scenario with no questions can't be drawn; the examiner will report the shortfall.
