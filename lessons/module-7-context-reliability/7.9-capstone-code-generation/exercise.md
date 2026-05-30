# Capstone — Code Generation with Claude Code — exercise

## What you're building

This is a **design exercise**, not a coding exercise — there is no `starter/` and no `pytest`. You'll architect a code-generation workflow for Claude Code operating on a large repository, and write it up as a design document. The rubric grades the document, not any code.

## The scenario

You're tasked with shipping a feature into a large, unfamiliar repository — pick one concretely so your design is specific, e.g.:

> Add **request rate limiting** to the public REST API of a ~400k-line backend monorepo you have never opened before. The change touches request middleware that every public route flows through.

(Use that one, or substitute your own large-repo feature — but keep it large-repo and keep at least one part of it high blast radius, so the plan-mode decision is real.)

## Your deliverable

Write your design to:

```
~/learn-claude-work/7.9/design.md
```

Create the directory if it doesn't exist (`mkdir -p ~/learn-claude-work/7.9`). The document must cover **all five** of the following, each as its own clearly-labeled section. Be concrete about *your* chosen task — name files, name commands, name the decision.

1. **Exploration strategy.** How you locate the change without reading the whole repo. Make the **search-first** move explicit (find before read), and **delegate the deep exploration to a subagent**: state the subagent's prompt (it inherits *only* the prompt string — no parent history) and exactly what findings it must return so the main context never holds the files it opened.

2. **Plan mode vs. direct execution.** State your decision criterion — **blast radius and reversibility**, not effort. Then apply it: which part(s) of your task go through **plan mode** (reviewed before edits hit disk) and which, if any, are safe to execute directly, and *why*. A high-risk change must go through plan mode.

3. **`CLAUDE.md` conventions to encode.** The concrete project norms you'd put in `CLAUDE.md` so generated code matches house style without re-stating it each turn — test/lint commands, layering/import rules, do-not-edit directories, key "we use X not Y" rules. Keep it tight (it sits in context every turn).

4. **Large-repo context strategy.** How you keep the main window lean on a repo bigger than any context window: search-over-read, subagent-delegated exploration, deliberate `@`-references, scoping the working set. Name the techniques and why each protects the budget.

5. **Verification / iteration loop.** The generate → run executable checks → feed failures back → correct → re-run loop. State the **objective** terminating condition (suite/build/lint green), not self-assessment.

## What your design must NOT do

The rubric grades one anti-pattern directly (`check: anti_pattern`):

- **Do NOT dump the whole codebase into context** ("read every file in `src/` first so you understand the project"), and **do NOT skip plan mode for the high-risk change.** A design that does either fails this criterion regardless of the rest.

## How to run it

There's nothing to execute — write `~/learn-claude-work/7.9/design.md` covering the five sections above, then:

```bash
/verify 7.9
```

and I'll grade the design against the rubric.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't; the worked example is the shape this exercise grades.
- [Claude Code — Common workflows](https://code.claude.com/docs/en/common-workflows) — search-first understanding and delegating exploration to subagents.
- [Claude Code — Permission modes](https://code.claude.com/docs/en/permission-modes) — plan mode.
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices) — `CLAUDE.md` and the iteration loop.
