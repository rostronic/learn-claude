---
chapter: "5.6"
slug: "iterative-refinement"
title: "Iterative refinement techniques"
module: "module-5-claude-code-mcp"
sequence: 21
references:
  - title: "Claude Code — Best practices"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "Verify-driven iteration, course-correction, /clear, failure patterns"
  - title: "Claude Code — Common workflows"
    url: "https://code.claude.com/docs/en/common-workflows"
    type: official_docs
    covers: "Course-correct with Esc/rewind, manage context, explore-plan-code"
  - title: "Claude Code — Choose a permission mode"
    url: "https://code.claude.com/docs/en/permission-modes"
    type: official_docs
    covers: "Plan mode as the explore phase of the refinement loop"
---

# Iterative refinement techniques

## Overview

Claude Code rarely produces the perfect result on the first shot for non-trivial
work — and it isn't meant to. The skill (CCAF 3.5) is running a **tight refinement
loop**: give Claude a way to check its own work, course-correct the moment it drifts,
and reset context when a session goes stale. Done well, the loop largely closes
*itself*; done badly, you become the slow part, re-reviewing a context window
polluted with failed attempts.

This lesson covers the documented techniques: **verify-driven iteration** (the
engine), **course-correction** (Esc / rewind / undo), and **context hygiene**
(`/clear`, the two-corrections rule). The throughline from the best-practices guide:
*"The best results come from tight feedback loops."*

## How it works

### Give Claude a check it can run

The single highest-leverage technique: *"Give Claude a check it can run: tests, a
build, a screenshot to compare. It's the difference between a session you watch and
one you walk away from"*
([best practices](https://code.claude.com/docs/en/best-practices)).

Why it matters: *"Claude stops when the work looks done. Without a check it can run,
'looks done' is the only signal available, and you become the verification loop…
Give Claude something that produces a pass or fail, and the loop closes on its own.
Claude does the work, runs the check, reads the result, and iterates until the check
passes."* The check is anything returning a readable signal — a test suite, a build
exit code, a linter, a screenshot diff.

The refinement primitive is therefore: **iterate while the check fails, stop when it
passes.** Note the parallel to agentic loops ([3.1](../../module-3-agentic-core/3.1-agentic-loops/lesson.md)):
the *real* stop signal is the check passing, not a fixed number of tries. An attempt
budget is a safety net against spinning forever, not the termination condition.

The best-practices guide sharpens the prompt itself:

| Strategy | Vague | Verifiable |
|---|---|---|
| Provide criteria | "validate email addresses" | "write validateEmail; user@example.com → true, invalid → false; run the tests after implementing" |
| Verify UI visually | "make the dashboard look better" | "[screenshot] implement this; screenshot the result, compare, list differences and fix them" |
| Fix root causes | "the build is failing" | "build fails with [error]; fix it, verify the build succeeds, address the root cause, don't suppress" |

### Course-correct early and often

When Claude drifts, intervene immediately — *"correcting it quickly generally
produces better solutions faster"*
([best practices](https://code.claude.com/docs/en/best-practices)):

- **`Esc`** — stop Claude mid-action; *"Context is preserved, so you can redirect."*
- **`Esc + Esc` or `/rewind`** — *"restore previous conversation and code state."*
  Claude snapshots files before each change, so you can try something risky and
  rewind if it doesn't pan out. (Not a git replacement — it only tracks Claude's
  changes.)
- **`"Undo that"`** — have Claude revert its changes.
- **`/clear`** — reset context between unrelated tasks.

### Context hygiene: when to reset

A session degrades as it fills — *"LLM performance degrades as context fills…
Claude may start 'forgetting' earlier instructions or making more mistakes."* Two
documented rules:

1. **Reset between unrelated tasks.** *"Use /clear frequently between tasks to reset
   the context window entirely."* The "kitchen sink session" — task A, then an
   unrelated question, then back to A — is a named failure pattern.
2. **Reset after repeated correction.** *"If you've corrected Claude more than twice
   on the same issue in one session, the context is cluttered with failed
   approaches. Run /clear and start fresh with a more specific prompt that
   incorporates what you learned. A clean session with a better prompt almost always
   outperforms a long session with accumulated corrections."*

The insight in rule 2: after two failed corrections, the problem usually isn't the
next correction — it's that the polluted context is now *causing* mistakes. The fix
is a fresh session plus a sharper prompt, not a third correction.

### The macro loop

Zooming out, refinement nests inside the explore → plan → code → commit workflow
([5.4](../5.4-plan-mode/lesson.md)): explore in plan mode, get a plan, implement
against a check, and iterate until the check passes. Refinement is the inner loop;
plan mode is how you avoid refining the *wrong* thing.

## Worked example: refining a flaky validator

You ask Claude to implement `validateEmail`. Run the loop the documented way:

1. **Make the goal verifiable.** Don't say "validate emails." Say: *"write
   validateEmail. Tests: user@example.com → true, invalid → false, user@.com →
   false. Run the tests after implementing."* Now Claude has a pass/fail signal.
2. **Let the loop close itself.** Claude writes the function, runs the tests, sees
   `user@.com` still passes when it shouldn't, fixes the regex, reruns — and stops
   when the suite is green. You didn't review intermediate attempts; the check did.
3. **Course-correct if it drifts.** It starts "fixing" the test instead of the code?
   `Esc`, redirect ("don't change the tests; fix the function"). Context preserved.
4. **Reset if it stalls.** Two corrections in and it's still wrong? The context is
   now cluttered with dead ends. `/clear`, and restart with a prompt that bakes in
   what you learned ("the bug is in the local-part check; emails like `user@.com`
   must fail"). The clean session beats a third correction.

Every move maps to a documented technique: a verifiable check to drive the loop,
`Esc` to course-correct, `/clear` after two failed corrections.

## Anti-patterns & pitfalls

**No check — you become the verification loop.** Without a test/build/screenshot,
"looks done" is the only stop signal and every mistake waits for you to notice it.
This is the "trust-then-verify gap" failure pattern. Always give Claude something
that returns pass/fail; *"if you can't verify it, don't ship it."*

**Correcting endlessly instead of resetting.** Past two corrections on the same
issue, the context is polluted with failed approaches that actively cause more
mistakes. `/clear` and re-prompt — don't pile on a third, fourth, fifth correction.

**The kitchen-sink session.** Threading unrelated tasks through one long
conversation fills context with irrelevant content and degrades performance. `/clear`
between unrelated tasks.

**Iterating on a fixed count instead of the check.** Stopping after "3 tries"
whether or not the check passes (or burning the whole budget when it already passed)
misuses the loop. The check passing is the real stop signal; the attempt cap is only
a runaway guard — the same principle as `stop_reason` in agentic loops.

**Vague prompts when you need precision.** "Make it better" gives Claude nothing to
verify against and invites the wrong fix. Scope the task, point to files with `@`,
and state what "done" looks like.

## Exam focus

CCAF 3.5 rewards the *progressive-improvement* discipline: drive iteration with a
**verifiable check** (tests/build/screenshot) so the loop closes itself;
**course-correct** with `Esc` / `/rewind` / "undo"; and practice **context hygiene**
— `/clear` between unrelated tasks and after **two** failed corrections on the same
issue. The reliable distractors are "keep correcting in the same session no matter
what" and "iterate a fixed number of times" — both ignore that a clean context plus a
pass/fail check is what actually converges.

## References & further reading

- [Best practices](https://code.claude.com/docs/en/best-practices) — "give Claude a
  way to verify its work," course-correction, `/clear`, and the named failure
  patterns.
- [Common workflows](https://code.claude.com/docs/en/common-workflows) — Esc/rewind
  course-correction, managing context, and the explore-plan-code recipe.
- [Choose a permission mode](https://code.claude.com/docs/en/permission-modes) —
  plan mode as the explore phase that keeps you from refining the wrong thing.

## Exam coverage

- **CCAF** — Domain 3 (Claude Code & Configuration), Task Statement 3.5: Apply
  iterative refinement techniques for progressive improvement.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
