# Learn Claude — Claude Code session context

Supplemental context for Claude Code sessions working *on* this repo (as opposed to a learner using it). The root [CLAUDE.md](../CLAUDE.md) is the editorial constitution; this file is the operational map.

## Where we are: the five-phase roadmap

This repo is being built in phases. Know which phase you're in before adding anything.

| Phase | What gets built | Status |
|---|---|---|
| **1** | Skeleton: `/study`, `/exercise`, `/verify` (manual), one lesson (1.1) end-to-end, curriculum map | **current** |
| **2** | Verifier subagent + grading MCP server — automated rubric checks replacing the manual `/verify` | planned |
| **3** | Examiner subagent + question bank + `/practice` (single Q) and `/mock-exam` (full timed run) | planned |
| **4** | Coach subagent as hub-and-spoke coordinator over verifier + examiner + progress-tracking MCP server | planned |
| **5** | Authoring commands (`/new-lesson`, `/new-question`) + full content build-out for all 37 lessons | planned |

Each phase reinforces a CCA-F domain that the platform itself teaches — see [docs/curriculum-map.md](../docs/curriculum-map.md). Don't pull Phase N+1 work forward unless asked.

## Slash command authoring conventions

All commands live in [.claude/commands/](commands/). Each is a single markdown file (`<name>.md`) whose body is the prompt Claude Code expands when the user types `/<name>`.

- **Commands take an optional argument.** The convention across this repo is a **lesson ID** in dotted form: `1.1`, `2.3`, `4.6`. Inside the command body, reference it as `$ARGUMENTS`.
- **Locate lessons by glob:** `lessons/**/<id>-*/`. Lesson directories are named `<id>-<slug>` (e.g. `1.1-agentic-loops`) so the ID prefix is the durable key.
- **Be conversational, not mechanical.** A command should *use* the file it finds, not dump it. `/study` walks the user through the lesson; it doesn't `cat` it.
- **Always end by suggesting the next step.** `/study` → `/exercise`. `/exercise` → `/verify`. `/verify` → next lesson or remediation.

## `/verify` in Phase 1 vs. Phase 2

**Phase 1 (now):** `/verify` is a manual placeholder. Claude reads the rubric, reads the user's work in `~/learn-claude-work/<id>/`, runs `pytest`, and grades each criterion by inspection. This works but is inconsistent across sessions.

**Phase 2:** `/verify` will delegate to a dedicated `verifier` subagent backed by a grading MCP server. The rubric schema is designed to support this — `check: code_review | anti_pattern | bash_execution` is what the verifier will dispatch on. Keep that schema stable through Phase 1 so Phase 2 has no migration to do.

## Where user work lives

Exercises copy their `starter/` directory to `~/learn-claude-work/<lesson-id>/` so the user can edit freely without dirtying this repo. `/verify` reads from there. Don't change this path without updating all three commands and the lesson `exercise.md` instructions in lockstep.

`/study` also seeds `~/learn-claude-work/<lesson-id>/` — but **non-destructively**: it copies the starter only when the dir is empty, so re-running `/study` to review a lesson never clobbers in-progress work. The division of labor: `/study` ensures a workspace exists so the learner can experiment while reading; `/exercise` is the explicit "set up / reset my workspace" step and prompts before overwriting existing work.
