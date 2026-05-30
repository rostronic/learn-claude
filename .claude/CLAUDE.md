# Learn Claude — Claude Code session context

Supplemental context for Claude Code sessions working *on* this repo (as opposed to a learner using it). The root [CLAUDE.md](../CLAUDE.md) is the editorial constitution; this file is the operational map.

## Where we are: the five-phase roadmap

This repo is being built in phases. Know which phase you're in before adding anything.

| Phase | What gets built | Status |
|---|---|---|
| **1** | Skeleton: `/study`, `/exercise`, `/verify` (manual), first lessons end-to-end, curriculum map | done |
| **2** | Verifier subagent + grading MCP server — automated rubric checks replacing the manual `/verify` | done |
| **3** | Examiner subagent + question bank + `/practice` (single Q) and `/mock-exam` (full timed run) | done |
| **4** | Coach subagent as hub-and-spoke coordinator over verifier + examiner + progress-tracking MCP server | **current** (coach + `/coach` built; progress-tracking MCP in progress) |
| **5** | Authoring commands (`/new-lesson`, `/new-question`) + full content build-out for all 37 lessons | **in progress** (`/new-lesson` + `/new-question` built; content build-out remaining) |

Each phase reinforces a CCA-F domain that the platform itself teaches — see [docs/curriculum-map.md](../docs/curriculum-map.md). Don't pull Phase N+1 work forward unless asked.

## Slash command authoring conventions

All commands live in [.claude/commands/](commands/). Each is a single markdown file (`<name>.md`) whose body is the prompt Claude Code expands when the user types `/<name>`.

- **Commands take an optional argument.** The convention across this repo is a **chapter id** in `module.lesson` form: `3.1`, `5.2`, `7.10` — the learning-path course order, **not** an exam's numbering. Inside the command body, reference it as `$ARGUMENTS`. Two commands are the exception: `/exam` and `/mock-exam` take an **exam code** (e.g. `CCAF`), because an exam is an overlay on the course, not a chapter.
  - chapter id: `/study`, `/exercise`, `/verify`, `/practice`, `/new-lesson`
  - exam code: `/exam`, `/mock-exam`, `/coach` (the exam to coach *toward*, default `CCAF`)
  - either: `/new-question` takes a **chapter id** (→ that chapter's `practice.yaml`) *or* an **exam code** (→ the mock-exam bank), and branches on which it got
- **Locate lessons by glob:** `lessons/**/<chapter>-*/`. Lesson directories are named `<chapter>-<slug>` (e.g. `3.1-agentic-loops`) so the chapter prefix is the lookup key. (Chapters are renumbered if the learning path is reordered; exam alignment lives in `docs/exam-mapping.md`.) Per-lesson practice questions live alongside the lesson at `lessons/**/<chapter>-*/practice.yaml`; the mock-exam question bank lives at top-level `exams/<CODE>/` (`exam.yaml` config + `questions/*.yaml`).
- **Be conversational, not mechanical.** A command should *use* the file it finds, not dump it. `/study` walks the user through the lesson; it doesn't `cat` it.
- **Always end by suggesting the next step.** `/study` → `/exercise`. `/exercise` → `/verify`. `/verify` → next lesson or remediation. `/practice` → another question or `/verify`. `/mock-exam` → review the weak domains' chapters, then re-run.

### The `examiner` subagent (Phase 3)

`/practice` and `/mock-exam` both delegate to the read-only [`examiner` subagent](agents/examiner.md) (`subagent_type: examiner`, tools: Read/Glob/Grep). Its reason to exist is **context isolation**: the examiner reads the question files — which contain the `correct` letter and `explanation` — so the **main conversation never holds the answer key while the learner is answering**. The command stays blind; the learner answers honestly.

The examiner runs in three modes the command selects explicitly: **PRESENT** (return one practice question — stem + options only), **ASSEMBLE** (pick 4 of 6 scenarios and build a domain-weighted ~30-question mock set — stems + options only), and **GRADE** (given the learner's collected `{id, answer}` pairs, reveal correct answers + explanations and compute the score). PRESENT and ASSEMBLE are forbidden from emitting `correct`/`explanation`; only GRADE reveals, and only because the learner's submitted answers are its input. The interactive turn-taking (show question → wait for the letter → reveal) happens in the **main loop** of the command, because a subagent can't pause for live input — the examiner is the leak-proof question store and scorer, not the conversationalist.

Mock-exam scoring is **scaled 100–1000, pass 720**: `scaled = round(1000 × domain-weighted fraction correct)`, with domain weights from `exam.yaml` (CCA-F: D1 27, D2 18, D3 20, D4 20, D5 15). This is documented as an *approximation* of Anthropic's scaled model, not the official algorithm. Mock-exam results persist to `~/learn-claude-work/mock-exams/<CODE>/<UTC-timestamp>.md` — user data, **outside the repo, never committed** (mirrors where `/verify` writes its per-chapter results).

### The `coach` subagent + `/coach` command (Phase 4) — hub-and-spoke, and why the command is the hub

`/coach <CODE>` turns a learner's history into "here's exactly what to do next." It's split deliberately into two pieces, and **the split is itself a Domain 1 lesson the platform dogfoods** (coordinator/subagent depth, chapters 3.2/3.3):

- **[`coach` subagent](agents/coach.md)** (`subagent_type: coach`, tools: Read/Glob/Grep + the progress MCP's read tool) is a **read-only ANALYSIS spoke**. It reads the learner's progress and the curriculum/exam maps and returns a **prioritized study plan** (snapshot, mock-exam readiness, an ordered `study`/`practice`/`verify`/`mock-exam` to-do list over **built** chapters, and which gaps are still planned-only). It does **not** grade and does **not** spawn anything.
- **[`/coach` command](commands/coach.md)** is the **hub-and-spoke coordinator, running in the main loop**. It spawns the `coach` for the analysis, then *acts* on the plan — pointing the learner at `/study`/`/practice`/`/verify`/`/mock-exam`, and where useful **spawning the `verifier` or `examiner` subagents directly** to grade or quiz on the spot.

**Why the coordinator lives in the command, not the coach subagent:** *a subagent cannot spawn another subagent.* That's a hard platform constraint — the exact coordinator/subagent depth limit chapters 3.2/3.3 teach. The roadmap calls the coach a "hub-and-spoke coordinator over verifier + examiner," but a `coach` *subagent* literally could not spawn the verifier or examiner. So the hub is the **command** (the main loop can spawn subagents); the coach is a leaf analysis spoke that *recommends* actions the hub carries out. If you ever feel tempted to give the coach an Agent tool so it can "just run the verifier itself," don't — you'd be building the depth-2 spawn the cert tests you for knowing is impossible.

**Progress source — MCP-first, filesystem fallback** (mirrors the verifier's MCP/Bash split): the coach prefers the **progress-tracking MCP server** (`infra/progress-mcp/`, exposing `get_progress` + `record_*`) via its `get_progress` tool when registered. When it isn't, the coach reconstructs the same picture from disk — `~/learn-claude-work/progress.json` (the record the MCP server persists), the per-chapter `results/<timestamp>.md` (verify scores, passing ≥80), and `mock-exams/<CODE>/<timestamp>.md` (scaled scores + weak domains) — plus `docs/curriculum-map.md` (built vs. planned) and `docs/exam-mapping.md` (domain/task → chapter). The plan is the same either way; only the transport differs. The coach **only ever recommends a built chapter** as an action; weaknesses whose chapters are still planned are surfaced as a ceiling, not a step.

### The authoring commands `/new-lesson` + `/new-question` (Phase 5)

These are the **authoring/infra** commands a contributor (human or Claude) uses to *build* coursework — not learner commands. They are guided scaffolders: they produce a structurally-valid skeleton and then coach the author to fill it per the rules, **never inventing lesson prose, code, or exam-scope content** (that's the content build-out, a separate task). Both end by pointing at the relevant audit + next step.

- **[`/new-lesson <chapter>`](commands/new-lesson.md)** — looks the chapter up in `docs/curriculum-map.md` (title/module) and `docs/exam-mapping.md` (CCAF domain/task, or unmapped), refuses to clobber an already-built chapter, then scaffolds `lessons/<module-dir>/<chapter>-<slug>/` with `lesson.md` (valid frontmatter + the six-section structure + an "## Exam coverage" footer **iff** mapped), `exercise.md`, `rubric.yaml` (chapter-keyed, weights sum to 100, ≥1 `anti_pattern`, a `bash_execution` pytest criterion), and a `starter/` (skeleton `.py` + skipped placeholder test + `requirements.txt` that compiles). It then walks the author through filling each piece and tells them to run the **`lesson-auditor`** and flip the chapter to **built** in both `docs/` maps. The starter module is named snake_case from the slug; the rubric's `bash_execution` `command` and the test filename stay in sync with it.
- **[`/new-question <chapter|CODE>`](commands/new-question.md)** — the argument decides the home: a **chapter id** appends to that chapter's `lessons/**/<chapter>-*/practice.yaml` (creating it with the `chapter:`/`questions:` header if absent); an **exam code** adds to the mock-exam bank `exams/<CODE>/questions/scenario-<N>-*.yaml` (it asks which scenario). It scaffolds entries in the **shared question schema** (stem / A–D / `correct` / `explanation` + `exam`/`domain`/`task_statement`/`scenario`), assigns the next free id by convention (`<exam>-d<domain>-<task>-NNN`, `…-practice-NNN` for practice), and enforces the question-authoring rules (one correct + three plausible-but-wrong distractors, an `explanation` that refutes each, every question traceable to the guide). For the bank it reminds the author to keep all six scenarios populated so `/mock-exam` can draw any 4 of 6.

Both leave the answer key in the author's hands, not the examiner's path — these *write* the files the examiner later serves; they don't administer anything.

## Infrastructure vs. coursework (load-bearing)

This repo is two things at once: **coursework** an end user studies, and the **infrastructure** that delivers and grades it. Keep them physically separate so a learner browsing the repo sees lessons, not plumbing — and so infra can change without touching content.

- **Coursework (learner-facing):** `lessons/` (the chapters), `docs/curriculum-map.md` + `docs/exam-mapping.md` (what to study and in what order), and the learner commands `/study`, `/exercise`, `/verify`, `/exam`.
- **Infrastructure (not coursework):** authoring/QA agents (`.claude/agents/` — e.g. `lesson-auditor`, `curriculum-auditor`), authoring rules (`.claude/rules/`), and any **build/grading services or scripts**. Grading/verification services (the Phase 2 grading MCP server and anything like it) live in a top-level **`infra/`** directory — **never under `lessons/`**. A lesson's `starter/` contains only what the learner runs; graders and servers do not ship inside a chapter.

Rule of thumb: if an end user would `pip install` and run it as part of an exercise, it's coursework and belongs in that chapter's `starter/`. If it exists to *operate the platform* (grade, audit, build, serve), it's infrastructure and belongs in `infra/` or `.claude/`, outside `lessons/`.

## `/verify` in Phase 1 vs. Phase 2

**Phase 1 (historical):** `/verify` was a manual placeholder — Claude read the rubric and the user's work inline and graded each criterion by inspection. This worked but was inconsistent across sessions.

**Phase 2 (now — implemented):** `/verify` delegates to the dedicated [`verifier` subagent](agents/verifier.md). The command itself just sanity-checks the chapter exists, spawns the verifier (`subagent_type: verifier`) with the chapter id, then logs the returned report to `~/learn-claude-work/<chapter>/results/<UTC-timestamp>.md` and suggests a next step. It does not grade inline. The verifier dispatches each criterion on its `check` (`code_review | anti_pattern | bash_execution`) and returns a weighted `N/100` report; it never edits the learner's code.

`bash_execution` criteria run their `command` in the learner's work dir through the **grading MCP server** (`infra/grading-mcp/`) when its tools are registered this session, and fall back to the **Bash tool** otherwise — the grade is identical either way. The rubric schema (`chapter` + `criteria[].{id,description,weight,check,command}`) is the stable contract between the rubric authors and the verifier; don't change it without updating both.

## Where user work lives

Exercises copy their `starter/` directory to `~/learn-claude-work/<lesson-id>/` so the user can edit freely without dirtying this repo. `/verify` reads from there. Don't change this path without updating all three commands and the lesson `exercise.md` instructions in lockstep.

`/study` also seeds `~/learn-claude-work/<lesson-id>/` — but **non-destructively**: it copies the starter only when the dir is empty, so re-running `/study` to review a lesson never clobbers in-progress work. The division of labor: `/study` ensures a workspace exists so the learner can experiment while reading; `/exercise` is the explicit "set up / reset my workspace" step and prompts before overwriting existing work.
