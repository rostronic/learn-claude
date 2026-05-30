---
chapter: "5.4"
slug: "plan-mode"
title: "Plan mode vs direct execution"
module: "module-5-claude-code-mcp"
sequence: 19
references:
  - title: "Claude Code — Choose a permission mode"
    url: "https://code.claude.com/docs/en/permission-modes"
    type: official_docs
    covers: "plan mode behavior, the approval flow, entering plan mode, defaultMode"
  - title: "Claude Code — Best practices (Explore, then plan, then code)"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "When planning pays off vs when to act directly"
  - title: "Claude Code — Common workflows (Plan before editing)"
    url: "https://code.claude.com/docs/en/common-workflows"
    type: official_docs
    covers: "Plan mode in the four-phase workflow"
---

# Plan mode vs direct execution

## Overview

Claude Code can change files, run commands, and work autonomously. Sometimes you
want that immediately; sometimes you want to *see the plan first*. **Plan mode** is
the permission mode for the second case: *"Claude reads files, runs shell commands
to explore, and writes a plan, but does not edit your source"*
([permission modes](https://code.claude.com/docs/en/permission-modes)).

CCAF 3.4 is a judgment task: knowing **when** to plan and when to just do it. The
exam isn't testing that you can press `Shift+Tab` — it's testing that you reach for
plan mode on the right tasks (and *don't* burn it on a typo fix). This lesson covers
what plan mode actually does, how the approval flow works, and the documented
heuristic for choosing.

## How it works

### What plan mode does (and doesn't)

Plan mode sits among Claude Code's permission modes. The relevant ones:

| Mode | Runs without asking |
|---|---|
| `default` | Reads only |
| `plan` | Reads only — and makes **no edits**, just proposes a plan |
| `acceptEdits` | Reads, file edits, common filesystem commands |

Per the docs: *"Plan mode tells Claude to research and propose changes without
making them. Claude reads files, runs shell commands to explore, and writes a plan,
but does not edit your source. Permission prompts still apply the same as default
mode."* So plan mode is a **read/analyze-only** posture: Claude can explore the
codebase freely and produce a concrete plan, but your working tree is safe — nothing
is written until you approve.

### Entering and approving

You enter plan mode three ways: press `Shift+Tab` to cycle into it, prefix a single
prompt with `/plan`, or start the session with `claude --permission-mode plan`.

When the plan is ready, *"Claude presents it and asks how to proceed."* Your options:

- Approve and start in auto mode
- Approve and accept edits
- Approve and review each edit manually
- Keep planning with feedback

*"Approving a plan exits plan mode and switches the session to the permission mode
each approve option describes, so Claude starts editing."* You can also press
`Ctrl+G` to open the proposed plan in your editor and refine it before Claude
proceeds. To make planning the default for a project, set `defaultMode: "plan"` in
`.claude/settings.json`.

The mental model: **plan mode separates *deciding what to do* from *doing it*,** with
an explicit human approval gate between them.

### The recommended workflow

The best-practices guide builds plan mode into a four-phase loop: *"Explore first,
then plan, then code."* *"Letting Claude jump straight to coding can produce code
that solves the wrong problem. Use plan mode to separate exploration from
execution."*

1. **Explore** — in plan mode, have Claude read the relevant code and answer
   questions, making no changes.
2. **Plan** — ask for a detailed implementation plan; edit it directly with `Ctrl+G`
   if needed.
3. **Implement** — leave plan mode and let Claude code against the approved plan.
4. **Commit** — descriptive message and a PR.

### When to plan vs act directly

Plan mode has a cost, and the docs say so plainly: *"Plan mode is useful, but also
adds overhead. For tasks where the scope is clear and the fix is small (like fixing
a typo, adding a log line, or renaming a variable) ask Claude to do it directly."*

And when it pays off: *"Planning is most useful when you're uncertain about the
approach, when the change modifies multiple files, or when you're unfamiliar with the
code being modified. If you could describe the diff in one sentence, skip the plan."*

That gives a clean decision rule. **Plan when any of these hold:**

- you're uncertain about the approach,
- the change spans multiple files,
- you're unfamiliar with the code.

**Otherwise act directly** — especially if you could describe the diff in one
sentence (typo, log line, rename).

## Worked example: applying the heuristic

Four tasks land on your desk. Where does each go?

1. **"Fix the typo in the dashboard header."** One file, scope obvious, one-sentence
   diff. → **Direct execution.** Plan mode would be pure overhead.
2. **"Add Google OAuth login."** New auth flow, touches session handling, callbacks,
   env config, multiple files, and you're not 100% on the existing session code. →
   **Plan mode.** Explore the auth code first, get a plan, review it, *then* let
   Claude implement. This is the OAuth example the docs use for the four-phase
   workflow.
3. **"Rename `getUser` to `fetchUser` across the service."** Mechanical, but it spans
   many files. Multiple files → **plan mode** (or at least review), so you can see
   the full set of call sites before they change rather than discovering a missed one
   after.
4. **"Add a log line in the request handler."** One file, one sentence. → **Direct.**

Notice the rule does the work: (1) and (4) fail every "plan" trigger and are
one-sentence diffs, so act directly; (2) trips all three triggers; (3) trips the
multi-file trigger. You're not guessing — you're applying the documented criteria.

## Anti-patterns & pitfalls

**Skipping the plan on a sprawling, unfamiliar change.** Letting Claude jump
straight to coding a multi-file feature in code you don't know "can produce code
that solves the wrong problem." When you're uncertain, multi-file, or unfamiliar:
plan first. Diving straight in is the headline mistake this task statement tests.

**Using plan mode for a one-line fix.** Plan mode adds overhead. Forcing the
explore-plan-approve cycle for a typo or a log line wastes turns and your attention
for no benefit. If you can describe the diff in one sentence, skip it.

**Thinking plan mode just "asks before editing."** It doesn't edit *at all* — it's
read/analyze-only and produces a plan you approve. It's not the same as `acceptEdits`
(which writes without prompting) or default mode (which prompts per action). Confusing
plan mode with a permission *prompt* is a classic distractor.

**Treating the plan as binding.** The plan is a reviewable artifact — edit it
(`Ctrl+G`) before approving, or keep planning with feedback. Approving it is a
deliberate gate, not a rubber stamp; that gate is the whole value.

## Exam focus

CCAF 3.4 is a *when* question. Expect scenarios that describe a task and ask whether
to plan or execute directly. Anchor on the documented triggers — **uncertain
approach, multi-file change, or unfamiliar code → plan; clear-scope one-sentence diff
→ direct.** Secondary facts that show up: plan mode is **read-only / makes no edits**,
you enter it with `Shift+Tab` / `--permission-mode plan`, and approving it switches to
an editing mode. The reliable distractors are "always plan everything" (ignores the
overhead) and "plan mode is just a confirmation prompt" (it makes no edits at all).

## References & further reading

- [Choose a permission mode](https://code.claude.com/docs/en/permission-modes) — what
  plan mode does, the approval options, entering it, and `defaultMode`.
- [Best practices — Explore, then plan, then code](https://code.claude.com/docs/en/best-practices)
  — the four-phase workflow and the explicit "when to plan vs act directly" callout.
- [Common workflows — Plan before editing](https://code.claude.com/docs/en/common-workflows)
  — plan mode in everyday recipes.

## Exam coverage

- **CCAF** — Domain 3 (Claude Code & Configuration), Task Statement 3.4: Determine
  when to use plan mode vs direct execution.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
