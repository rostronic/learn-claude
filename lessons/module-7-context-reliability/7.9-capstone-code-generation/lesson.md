---
chapter: "7.9"
slug: "capstone-code-generation"
title: "Capstone — Code Generation with Claude Code"
module: "module-7-context-reliability"
sequence: 36
references:
  - title: "Claude Code — Common workflows"
    url: "https://code.claude.com/docs/en/common-workflows"
    type: official_docs
    covers: "Search-first codebase understanding, delegating research to subagents, plan-before-editing"
  - title: "Claude Code — Working with large codebases"
    url: "https://code.claude.com/docs/en/large-codebases"
    type: official_docs
    covers: "Configuring Claude Code for monorepos and large repositories"
  - title: "Claude Code — Permission modes"
    url: "https://code.claude.com/docs/en/permission-modes"
    type: official_docs
    covers: "Plan mode and other permission modes — analyze before editing disk"
  - title: "Agent SDK — Subagents"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Fresh per-subagent context, context isolation, what subagents inherit"
  - title: "Claude Code — Best practices"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "CLAUDE.md conventions, context management, iterative refinement"
---

# Capstone — Code Generation with Claude Code

## Overview

This capstone is the synthesis chapter for **CCA-F Scenario 2 — Code Generation with Claude Code**. The setup is the one every working engineer recognizes: a large, unfamiliar repository — a monorepo, or a service with hundreds of thousands of lines — and a feature to ship inside it. The wrong instinct is to make Claude *read the whole thing* so it "understands the codebase." That instinct is exactly what this chapter trains you out of.

The scenario ties together four task statements you've met separately in this module and earlier ones, and the exam tests whether you can compose them under one workflow:

- **5.4 — large-codebase context management**: keep the main context window clean on a repo far bigger than any window.
- **3.1 — CLAUDE.md configuration**: encode project norms so generated code matches the house style without you re-stating it each turn.
- **3.4 — plan mode vs. direct execution**: review a plan before edits touch disk on risky changes; act directly on trivial, well-scoped ones.
- **3.5 — iterative refinement**: drive a verify-and-correct loop instead of one-shotting.

The deliverable for the exercise is a written **design** of a code-generation workflow on a large repo — an architecture decision, not a hand-built script. There is no `pytest` here. What the exam (and the rubric) check is whether your workflow keeps context lean, gates risk with plan mode, steers generation with `CLAUDE.md`, and closes the loop with verification. The single biggest failure mode — and the one anti-pattern the rubric grades hardest — is *dumping the entire codebase into context* and/or *skipping plan mode on a high-risk change*. Both are wrong on this exam, and we'll say so plainly.

## How it works

The workflow has five moving parts. Treat them as a pipeline: explore narrowly, decide how to act, encode the rules, manage the budget, then loop until verified.

### (a) Search-first exploration, and delegate it to subagents

The foundational move on a large repo is to **find** before you **read**. Claude Code's own guidance for understanding a new codebase is to *start broad and then narrow*: ask for an overview, then ask targeted questions like "find the files that handle user authentication" rather than opening files at random ([Common workflows](https://code.claude.com/docs/en/common-workflows)). Search (Grep/Glob) returns line-scoped hits; reading pulls whole files into the window. On a large repo the difference is the whole ballgame — search touches the 8 files that matter, reading touches the 800 that don't.

But even search-then-read pollutes the *main* context: every file Claude opens to confirm a hit stays in the window for the rest of the session. The prescribed fix is to **delegate the exploration to a subagent**. As the docs put it: "Exploring a large codebase fills your context with file reads. Delegate the exploration so only the findings come back" ([Common workflows — delegate research to subagents](https://code.claude.com/docs/en/common-workflows)). The mechanism is context isolation: "Each subagent runs in its own fresh conversation," and "intermediate tool calls and results stay inside the subagent; only its final message returns to the parent" ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). So a subagent can open thirty files, burn its own window understanding the auth flow, and hand the parent back a half-page summary — *the parent never holds the thirty files*.

One constraint that decides whether delegation works: the **only** parent→child channel is the prompt string you pass the subagent. It does not inherit the parent's conversation history ([Subagents — what subagents inherit](https://code.claude.com/docs/en/agent-sdk/subagents)). So you must hand it everything it needs to do the job cold — the question, the relevant paths, the conventions to honor — and it must hand back findings dense enough that the parent never needs to re-open the files. Design the subagent's return value as deliberately as its prompt.

### (b) Plan mode vs. direct execution

Once you know *where* the change goes, decide *how* to make it. **Plan mode** is the permission mode that lets Claude "analyze before you edit" — it explores and proposes a plan but is barred from writing to disk until you approve ([Permission modes](https://code.claude.com/docs/en/permission-modes)). It is the right default for any change where a wrong edit is expensive to undo: schema migrations, touching a widely-imported module, security-sensitive code, anything spanning many files. The docs frame planning before editing as a first-class workflow — explore and plan, *then* implement ([Common workflows — plan before editing](https://code.claude.com/docs/en/common-workflows)).

Direct execution is correct for the opposite case: trivial, well-scoped, low-blast-radius edits — a typo, a single new test, a localized helper — where the review overhead buys you nothing. The decision criterion is **blast radius and reversibility**, not effort: how many files/callers does this touch, how hard is it to revert, and how confident is the plan. High blast radius or low confidence → plan mode. Low blast radius and high confidence → direct.

The exam's trap here is symmetric. Skipping plan mode on a high-risk change is the headline anti-pattern of this scenario; but *insisting on plan mode for a one-line fix* is also wrong-on-this-exam — it's the friction that pushes people to disable review entirely. State your criterion and apply it both ways.

### (c) CLAUDE.md to steer generation toward project norms

`CLAUDE.md` is the project memory file Claude Code loads automatically — the place to encode the conventions that should shape *every* generated edit so you don't re-type them each turn ([Best practices](https://code.claude.com/docs/en/best-practices)). The right contents are the project-specific rules a new hire would otherwise learn by getting code review rejections: the test command and how to run a single test, the lint/format toolchain, import and layering conventions, "we use X not Y," directories that are generated and must not be hand-edited, and any load-bearing house patterns. Keep it tight — it sits in context every turn, so it competes for the budget you're trying to protect. Treat it as curated rules, not a dumping ground for the whole architecture doc.

This is the same lever as programmatic enforcement elsewhere on the exam: a convention written in `CLAUDE.md` is *configuration that always applies*, far more reliable than re-stating "remember to run black" in each prompt and hoping it sticks.

### (d) Context management on the large repo

On a repo far larger than any window, the budget *is* the constraint, and three techniques compound:

1. **Don't load what you can search.** Covered above — this is the first and biggest win.
2. **Push exploration into subagents** so file-reading cost is paid in a throwaway window, not the main one ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).
3. **Configure Claude Code for the repo's scale.** For monorepos and very large repositories there is explicit guidance on configuration ([Large codebases](https://code.claude.com/docs/en/large-codebases)) and on context management as a practice ([Best practices](https://code.claude.com/docs/en/best-practices)) — scope the working set ([Large codebases](https://code.claude.com/docs/en/large-codebases)), and lean on `@`-references to pull in *specific* files deliberately rather than letting the agent wander ([Common workflows — reference files and directories](https://code.claude.com/docs/en/common-workflows)).

The mental model: the window is a finite working set, not the repository. Your job is to keep the *relevant* slice resident and let everything else stay on disk, reachable by search.

### (e) The iterative-refinement + verification loop

Code generation is not one-shot. The loop is: generate → run the project's checks (tests, type-checker, linter — the commands you put in `CLAUDE.md`) → feed failures back → correct → re-run, until green ([Best practices](https://code.claude.com/docs/en/best-practices)). The verification step has to be *executable and objective* — the test suite passing, the build succeeding — not Claude's self-assessment that the code "looks right." Define the success criterion before you start so the loop has a terminating condition it can check, the same way an agentic loop terminates on a real signal rather than vibes.

## Worked example

Concrete task: **"Add rate limiting to the public REST API"** in a ~400k-line backend monorepo you've never opened. Here's the full workflow.

**1. Orient, broad then narrow.** Ask for an overview, then narrow: "Which package serves the public REST endpoints, and where does request middleware get registered?" This is search-first — you're locating the seam, not reading the service.

**2. Delegate the deep exploration.** Spawn an exploration subagent with a self-contained prompt:

> "In this repo, find how HTTP middleware is registered for the public API. Report back: the middleware-registration file and its path, the existing middleware in order, the config mechanism for per-route settings, and the test file that covers middleware. Do not propose changes."

The subagent opens a dozen files in its own window and returns a half-page of findings. Your main context gains the *map*, not the dozen files ([Common workflows](https://code.claude.com/docs/en/common-workflows), [Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). If the feature had two unknowns (say, middleware *and* the config system), you could run two subagents in parallel and merge their summaries.

**3. Encode norms in `CLAUDE.md`** (if not already present) so the generated code lands in-style:

```markdown
# Project conventions
- Tests: `make test`; single test: `pytest path::test_name`
- Lint/format: `make lint` (ruff + black) — must pass before done
- Middleware lives in `api/middleware/`, registered in `api/app.py`; one class per file
- Config is loaded from `config/settings.py` — never hardcode limits
- `api/generated/` is codegen output — do not hand-edit
```

**4. Choose the execution mode by blast radius.** Adding rate limiting touches request middleware that *every* public route flows through — high blast radius, hard to be sure it's right by inspection. So this goes through **plan mode**: Claude proposes the new middleware class, the registration change, the config keys, and the test, and you review that plan *before any edit hits disk* ([Permission modes](https://code.claude.com/docs/en/permission-modes)). You approve (or correct the plan and re-approve). Contrast: if the task were "fix the typo in the 429 error message," you'd let Claude edit directly — plan mode there is pure friction.

**5. Run the verification loop.** After the edits land, run `make test` and `make lint` (the commands `CLAUDE.md` named). Suppose two tests fail because the limiter rejects an internal health-check route. Feed the failures back; Claude exempts the health route and re-runs. Loop until tests and lint are green ([Best practices](https://code.claude.com/docs/en/best-practices)). The terminating condition is objective — the suite passes — not "looks done."

Read end to end: **search-first → subagent-delegated exploration → `CLAUDE.md`-steered generation → plan-mode review for a high-blast-radius change → executable verification loop.** The main context held a map and a plan, never the 400k lines.

## Anti-patterns & pitfalls

**Dumping the whole codebase into context.** "Read every file in `src/` so you understand the project, then add the feature." This is the headline anti-pattern of the scenario and the one the rubric grades hardest. It blows the window on a large repo, and even when it fits, accuracy degrades as irrelevant content crowds the window. The prescribed approach is search-first plus subagent-delegated exploration so "only the findings come back" ([Common workflows](https://code.claude.com/docs/en/common-workflows)) — there is no version of "load it all" that is correct on this exam.

**Skipping plan mode on a high-risk change.** Letting Claude edit a schema migration, a widely-imported module, or security code directly, with no plan to review before it writes to disk. Plan mode exists precisely to "analyze before you edit" ([Permission modes](https://code.claude.com/docs/en/permission-modes)); bypassing it on a high-blast-radius change is wrong. (The mirror error — forcing plan mode for a one-line fix — is also wrong; the criterion is blast radius and reversibility, applied both ways.)

**Exploring in the main context instead of a subagent.** Having the main agent open dozens of files to "investigate." Even when it fits the window, those reads stay resident and crowd out the actual work. Delegate exploration so the file-reading cost is paid in a throwaway window ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). A corollary trap: spawning a subagent but giving it a vague prompt or expecting it to inherit your history — it gets *only* the prompt string, so an under-specified delegation just fails silently and you re-do the work in the main window.

**Re-stating conventions in every prompt instead of `CLAUDE.md`.** Pasting "remember to run black, we use pytest, don't edit generated/" into each message. This is the prompt-instruction-over-configuration error: conventions belong in `CLAUDE.md` where they always apply ([Best practices](https://code.claude.com/docs/en/best-practices)), not in prose you hope sticks turn to turn.

**Treating generation as one-shot — no verification loop.** Accepting the first diff because it "looks right." Generated code must clear the project's *executable* checks (tests, types, lint), and failures feed back into a correction loop ([Best practices](https://code.claude.com/docs/en/best-practices)). Self-assessment is not verification; a passing suite is.

## Exam focus

This is **Scenario 2 — Code Generation with Claude Code**, and the questions are composition questions: they hand you a large-repo task and ask which *workflow* is correct. The reliable distractors are the anti-patterns above — "read the whole repo first," "let it edit the migration directly," "remind it of the conventions each turn." The correct answer is always the lean-context, risk-gated, convention-configured, verification-looped workflow: search and delegate over read-everything; plan mode for high blast radius, direct for trivial; `CLAUDE.md` over repeated prompting; an executable verification loop over one-shot acceptance.

Because it's a capstone, expect the four underlying task statements to be braided into a single stem — getting one part right (say, plan mode) but botching another (dumping the repo into context) is still the wrong overall answer.

## References & further reading

- [Claude Code — Common workflows](https://code.claude.com/docs/en/common-workflows) — understanding new codebases broad-then-narrow, finding relevant code by search, delegating research to subagents, and planning before editing. The spine of this capstone.
- [Claude Code — Working with large codebases](https://code.claude.com/docs/en/large-codebases) — configuring Claude Code for monorepos and very large repositories.
- [Claude Code — Permission modes](https://code.claude.com/docs/en/permission-modes) — plan mode and the other permission modes; analyze before you edit disk.
- [Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — fresh per-subagent context, context isolation ("only its final message returns to the parent"), and what a subagent does and does not inherit.
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices) — `CLAUDE.md` conventions, context management, and the iterative-refinement workflow.

## Exam coverage

- **CCAF** — Scenario 2: Code Generation with Claude Code. This capstone ties together Task Statements 5.4, 3.4, 3.1, and 3.5.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
