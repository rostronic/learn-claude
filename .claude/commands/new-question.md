Scaffold one or more assessment questions and guide the author to fill them in correctly.

The user invoked `/new-question $ARGUMENTS`. `$ARGUMENTS` selects **where the question lands**, and there are two forms:

- **A chapter id** (`module.lesson`, e.g. `3.1`) → append to that chapter's per-lesson **practice** bank, `lessons/**/$ARGUMENTS-*/practice.yaml`. Topic drills for one chapter.
- **An exam code** (uppercase, e.g. `CCAF`) → add to the **mock-exam bank**, `exams/$ARGUMENTS/questions/<scenario-file>.yaml`. Scenario questions with full metadata.

Tell them apart: a dotted `\d+\.\d+` is a chapter; an all-caps token is an exam code. If `$ARGUMENTS` is empty or ambiguous, ask which they mean and stop.

> **Authoring/infra command (Phase 5).** It writes into the question files the read-only `examiner` subagent later serves to `/practice` and `/mock-exam`. **Read `.claude/rules/question-authoring.md` now** — it's the contract, and it loads automatically when you edit these YAML files anyway. **Don't fabricate exam-scope content**: every question must trace to the exam guide (a specific task statement, and for the bank a scenario). You scaffold the schema and enforce the rules; the author supplies stems and options that are actually in scope.

## Step 1 — Resolve the target file

**Chapter form (`practice.yaml`):**
- `Glob` for `lessons/**/$ARGUMENTS-*/practice.yaml`.
- If the chapter directory exists but there's no `practice.yaml`, create one with a header:
  ```yaml
  # Per-lesson practice questions for chapter $ARGUMENTS.
  # Topic-only drills (no exam scenario) that test this chapter's material.
  chapter: "$ARGUMENTS"
  questions:
  ```
- If the chapter itself isn't built (`lessons/**/$ARGUMENTS-*/lesson.md` missing), stop and tell them to `/new-lesson $ARGUMENTS` first — questions drill a lesson that should exist.

**Exam form (bank):**
- Confirm `exams/$ARGUMENTS/exam.yaml` exists; if not, stop (that exam isn't set up).
- Read `exams/$ARGUMENTS/exam.yaml` for the domain weights, the domain names, and the **six scenarios**. The bank is organized one file per scenario: `exams/$ARGUMENTS/questions/scenario-<N>-<slug>.yaml`. Ask the author **which scenario** (1–6) and **which task statement / domain** the new question targets, then append to that scenario's file. List the existing scenario files so they can see the layout.

## Step 2 — Pick a stable, unique id

Convention: `<exam>-d<domain>-<task>-NNN` for the bank (e.g. `ccaf-d2-2.1-003`), and `<exam>-d<domain>-<task>-practice-NNN` for per-lesson practice (e.g. `ccaf-d1-1.1-practice-004`). `Grep` the target file (and, for the bank, the sibling scenario files) for existing ids with the same prefix and use the next free `NNN`. **Never reuse or renumber a published id** — the examiner and the Phase 4 progress tracker key off it.

## Step 3 — Scaffold the entry/entries

Append one YAML list item per question in the **shared schema**. Fill what you can from Step 1 (exam/domain/task_statement/scenario); leave `TODO(author):` markers for the judgement calls — the stem, the options, and which letter is correct. Keep the structure valid YAML so the examiner can load it immediately.

**Bank (exam form)** — full metadata required:

```yaml
- id: "<exam>-d<domain>-<task>-NNN"
  stem: >-
    TODO(author): a production-context multiple-choice question framed in scenario <N>.
    One clear question; no "which of the following EXCEPT" trickery.
  options:
    A: "TODO(author): option A"
    B: "TODO(author): option B"
    C: "TODO(author): option C"
    D: "TODO(author): option D"
  correct: "TODO(author): exactly one of A/B/C/D"
  explanation: >-
    TODO(author): justify the key AND refute each distractor — one clause per wrong
    option saying WHY it fails. A reveal that only praises the right answer is incomplete.
  exam: "<exam>"
  domain: <domain>                 # the single domain this question scores under (drives weighting)
  task_statement: "<task_statement>"
  scenario: <N>                    # 1–6
```

**Practice (chapter form)** — `exam`/`domain`/`task_statement` are optional (the chapter's mapping already lives in `docs/exam-mapping.md`); `scenario` is omitted for topic-only drills. Keep them if you know them — they're cheap and useful:

```yaml
  - id: "<exam>-d<domain>-<task>-practice-NNN"
    stem: >-
      TODO(author): a question that tests THIS chapter's material.
    options:
      A: "TODO(author): option A"
      B: "TODO(author): option B"
      C: "TODO(author): option C"
      D: "TODO(author): option D"
    correct: "TODO(author): exactly one of A/B/C/D"
    explanation: >-
      TODO(author): justify the key AND refute each distractor (one clause each).
    exam: "<exam>"               # optional for practice
    domain: <domain>            # optional for practice
    task_statement: "<task_statement>"   # optional for practice
```

(Match the indentation of the existing items in the file — bank files are top-level list items; `practice.yaml` nests under `questions:`.)

## Step 4 — Enforce the question rules while the author fills it

Coach the author through the `question-authoring.md` rules — these are non-negotiable and you should check each before considering the question done:

1. **Exactly one correct answer and three distractors.** Four options, A–D. `correct` is a single letter.
2. **Traces to the guide.** The `task_statement` (and, for the bank, the `scenario`) must be real and in scope. If the author is unsure it's testable, the answer is "read the exam guide," not "guess." No third-party sources, no out-of-scope trivia.
3. **Distractors are plausible-but-wrong** — the approaches a candidate with partial knowledge would actually pick. On this exam the best distractors are the **anti-patterns the lessons warn about** (prompt-based enforcement where programmatic is required, few-shot where a tool description is the fix, parsing text for loop termination, an iteration cap as the stop signal, …). The correct option is the prescribed "Anthropic way," not "it depends."
4. **The `explanation` justifies the key AND refutes each distractor** — one clause per wrong option. Mirror the official sample questions (`ccaf-d1-1.4-001`, `ccaf-d2-2.1-001`) for tone.
5. **`domain` is the single domain the question scores under** — pick the one task statement it most tests; that tag drives `/mock-exam` weighting.
6. **Don't touch the verbatim sample anchors.** The two official sample questions are copied exactly and tagged `source:`; never reword them.

## Step 5 — Coverage reminder + next step

- **Bank:** remind the author that `/mock-exam` assembles a run from **any 4 of the 6 scenarios**, weighted D1 27 / D2 18 / D3 20 / D4 20 / D5 15. After adding this one, point out which scenarios are thin or empty (a scenario with no questions can't be drawn — the examiner reports the shortfall) and suggest `/new-question $ARGUMENTS` again to even out coverage.
- **Practice:** a few solid drills per chapter is plenty; suggest another if the chapter has fewer than ~3.
- **Smoke-test it.** Once the author has filled the stem/options/`correct`/explanation, suggest running `/practice $ARGUMENTS` (chapter) or `/mock-exam $ARGUMENTS` (exam) — both route through the examiner, so it's the honest way to see the question render and grade. If anything in the YAML is malformed, the examiner will surface it.

## Tone

You're a question-bank scaffolder, not a quiz writer. Lay down valid, correctly-tagged schema fast, then hold the author to the rules — one correct answer, three real anti-pattern distractors, an explanation that refutes each, every question traceable to the guide. Don't invent the exam content yourself.
