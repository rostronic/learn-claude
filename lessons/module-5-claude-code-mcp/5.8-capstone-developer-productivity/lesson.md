---
chapter: "5.8"
slug: "capstone-developer-productivity"
title: "Capstone — Developer Productivity with Claude"
module: "module-5-claude-code-mcp"
sequence: 23
references:
  - title: "Claude Code — How Claude remembers your project (memory)"
    url: "https://code.claude.com/docs/en/memory"
    type: official_docs
    covers: "CLAUDE.md scopes, .claude/rules/ + paths, imports"
  - title: "Claude Code — Extend Claude with skills"
    url: "https://code.claude.com/docs/en/skills"
    type: official_docs
    covers: "Skills, invocation control for side-effecting workflows"
  - title: "Claude Code — Choose a permission mode"
    url: "https://code.claude.com/docs/en/permission-modes"
    type: official_docs
    covers: "Plan mode vs direct execution"
  - title: "Claude Code — Connect Claude Code to tools via MCP"
    url: "https://code.claude.com/docs/en/mcp"
    type: official_docs
    covers: "MCP scopes, .mcp.json, trust"
  - title: "Claude Code — GitHub Actions"
    url: "https://code.claude.com/docs/en/github-actions"
    type: official_docs
    covers: "claude-code-action, secrets, CI integration"
  - title: "Claude Code — Best practices"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "Iterative refinement, when to plan, scoping permissions"
---

# Capstone — Developer Productivity with Claude

## Overview

This capstone is the CCAF **Scenario 4: Developer Productivity with Claude**. The
five domains and seven task statements in this module each answered one question in
isolation; a scenario question hands you a *whole situation* and asks you to choose
the right mechanism for each requirement — and to reject the tempting-but-wrong one.

The scenario throughout: **a platform team is rolling Claude Code out to 60
engineers across a large monorepo.** They need shared conventions that scale,
language-specific rules that don't bloat context, reusable workflows, safe
automation in CI, and a database connection the whole team can use — without leaking
secrets or letting the model do something irreversible on its own. Every
requirement maps to a mechanism you've already learned; the skill is the *mapping*,
under the "Anthropic way" constraint that some answers are simply correct and their
alternatives simply wrong.

There's no new API surface here. This lesson re-walks the module's mechanisms as a
single coherent setup, names the decision rule for each, and the exercise has you
encode those mappings as a checkable plan.

## How it works: requirement → mechanism

Take the platform team's requirements one at a time.

**1. Repo-wide conventions every engineer shares.** ([5.1](../5.1-claudemd-hierarchy/lesson.md))
"All PRs target `develop`; run `make verify` before claiming done" is true for the
whole team and the whole repo. → **Project `./CLAUDE.md`**, checked in. Keep it lean
(*"target under 200 lines"*); org-wide policy that must hold for *every* repo on the
machine goes a layer up, in **managed-policy** memory. Personal "be terse" habits go
in each engineer's **`~/.claude/CLAUDE.md`**, never the shared file.

**2. Language-specific conventions that shouldn't load everywhere.** ([5.2](../5.2-path-specific-rules/lesson.md))
"Python wants type hints and `ruff`; the frontend wants Prettier." Putting both in
the root CLAUDE.md taxes every session with half-irrelevant rules. → **Path-scoped
rules** under `.claude/rules/` with a `paths:` glob, so the Python rule loads only
when Claude touches `**/*.py`. That's conditional convention loading, native.

**3. A rule that must hold absolutely.** ([5.2](../5.2-path-specific-rules/lesson.md))
"Generated `proto/` and `migrations/` are never hand-edited." A rule is *context*,
not enforcement. → A **`PreToolUse` hook** matched to `Edit|Write` that checks the
path and exits 2 (or returns `deny`). Programmatic enforcement over prompting — the
non-negotiable from Domain 1, applied here.

**4. Reusable team workflows.** ([5.3](../5.3-commands-and-skills/lesson.md))
"Everyone reviews PRs the same way; everyone files issues the same way." → **Skills**
(`.claude/skills/*/SKILL.md`), checked in so all 60 engineers get the same `/review-pr`.
And the deploy workflow? → a skill with **`disable-model-invocation: true`**, so
Claude can't trigger a production deploy on its own judgment.

**5. Knowing when to let Claude just go.** ([5.4](../5.4-plan-mode/lesson.md))
A one-line config fix → **direct execution**; a multi-file feature in unfamiliar
service code → **plan mode** first (explore → plan → approve → implement). Teach the
rule, not a blanket policy: plan when uncertain / multi-file / unfamiliar; act
directly on a one-sentence diff.

**6. A shared data connection.** ([5.5](../5.5-mcp-servers/lesson.md))
"Claude should answer questions against our analytics DB." → An **MCP server at
project scope** (checked-in `.mcp.json`) so the team shares it, with the DSN supplied
via **`${ANALYTICS_DSN}` env-var expansion** (never committed) and a **read-only**
credential (least privilege). Project servers require approval on first use — the
trust gate.

**7. Progressive improvement in daily work.** ([5.6](../5.6-iterative-refinement/lesson.md))
Engineers get better results by giving Claude a **check it can run** (the repo's test
suite / build) and letting the loop close itself, course-correcting with `Esc`, and
running `/clear` between unrelated tasks or after two failed corrections.

**8. Safe automation in CI.** ([5.7](../5.7-cicd-pipelines/lesson.md))
"Auto-review every PR; run nightly dependency checks." → The **`claude-code-action`**
GitHub Action (or headless `claude -p`), authenticated with **`${{ secrets.ANTHROPIC_API_KEY }}`**
(never a literal key), **tool-scoped** because it runs unattended, with a **human
reviewing before merge**.

The pattern across all eight: match the mechanism to the *kind* of requirement —
shared vs personal vs path-specific vs must-enforce vs side-effecting vs
unattended — and prefer the Anthropic-prescribed option (programmatic enforcement,
least privilege, secrets-not-literals, verify-driven iteration) over the seductive
shortcut.

## Worked example: the rollout plan

Here's the platform team's setup as one coherent configuration, each line traceable
to a requirement above:

```
repo/
├── CLAUDE.md                      # (1) repo-wide: branch policy, `make verify`
├── .mcp.json                      # (6) project MCP: analytics DB, DSN via ${ANALYTICS_DSN}
├── .claude/
│   ├── rules/
│   │   ├── python.md              # (2) paths: ["**/*.py"] — ruff, type hints
│   │   └── frontend.md            # (2) paths: ["web/**/*.{ts,tsx}"] — prettier, no console.log
│   ├── hooks/guard-generated.sh   # (3) PreToolUse Edit|Write -> exit 2 on proto/** , migrations/**
│   ├── skills/
│   │   ├── review-pr/SKILL.md     # (4) shared review workflow
│   │   └── deploy/SKILL.md        # (4) disable-model-invocation: true
│   └── settings.json              # registers the PreToolUse hook
└── .github/workflows/claude.yml   # (8) claude-code-action, ${{ secrets.ANTHROPIC_API_KEY }}
```

Plus the per-engineer pieces that *don't* live in the repo: each developer's
`~/.claude/CLAUDE.md` for personal style, and the local `ANALYTICS_DSN` env var that
fills the `.mcp.json` placeholder. And a habit, not a file: drive work with the
repo's test suite as the check, plan multi-file changes, act directly on small ones.

Walk the diff against the requirements and every choice has a reason: shared facts in
committed CLAUDE.md, language rules path-scoped so they don't bloat context, the
hard "don't touch generated code" rule in a hook (not prose), the deploy skill
locked to user-invocation, the DB shared at project scope with the secret kept out of
git, and CI authenticated through secrets with bounded permissions. That traceability
— requirement to mechanism to *why this and not the alternative* — is exactly what a
scenario question grades.

## Anti-patterns & pitfalls

These are the seductive wrong turns the scenario will offer. Each is the
already-covered anti-pattern, now in the rollout's clothing:

- **One giant root CLAUDE.md for everything** — Python rules, frontend rules, deploy
  runbook, personal style. Bloats every session and buries the rules that matter.
  Scope down (path rules) and pull personal prefs to user memory. (5.1)
- **"Never edit generated code" as a CLAUDE.md line.** Advisory; the model can still
  do it. A must-hold rule is a `PreToolUse` hook. (5.2)
- **A `/deploy` skill the model can auto-invoke.** It will deploy when the code
  "looks ready." `disable-model-invocation: true`. (5.3)
- **Always plan, or never plan.** Both ignore the rule. Plan multi-file/unfamiliar
  work; act directly on one-sentence diffs. (5.4)
- **DSN hard-coded in the committed `.mcp.json`.** Leaks the secret to everyone with
  repo access. Env-var expansion + least-privilege credential. (5.5)
- **Endless correcting in one polluted session / no check to verify against.** After
  two failed corrections, `/clear` and re-prompt; always give Claude a pass/fail
  check. (5.6)
- **API key pasted into the workflow YAML, or unbounded CI permissions.** Secrets,
  never literals; scope tools because no human approves; review before merge. (5.7)

If a scenario option embodies one of these, it's a distractor — by design.

## Exam focus

Scenario 4 questions read like the rollout above: a paragraph of context, then "what
should they do for X?" The winning answer is the mechanism whose *kind* matches the
requirement, and it's usually the Anthropic-prescribed one — programmatic enforcement
for hard rules (hook over prompt), least privilege for data and CI, secrets over
literals, `disable-model-invocation` for side-effecting commands, path-scoped rules
for conditional conventions, plan-when-uncertain. The distractors are this module's
anti-patterns dressed in scenario detail. Map requirement → kind → mechanism, and
reject the shortcut.

## References & further reading

- [Memory](https://code.claude.com/docs/en/memory) — CLAUDE.md scopes, `.claude/rules/`,
  imports (5.1, 5.2).
- [Skills](https://code.claude.com/docs/en/skills) — reusable workflows and
  invocation control (5.3).
- [Permission modes](https://code.claude.com/docs/en/permission-modes) — plan vs
  direct (5.4).
- [MCP](https://code.claude.com/docs/en/mcp) — shared servers, scopes, trust (5.5).
- [GitHub Actions](https://code.claude.com/docs/en/github-actions) — CI integration
  and secrets (5.7).
- [Best practices](https://code.claude.com/docs/en/best-practices) — iterative
  refinement and permission scoping (5.6, 5.7).

## Exam coverage

- **CCAF** — Scenario 4: Developer Productivity with Claude. This capstone integrates
  Domain 3 (Task Statements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6) and Domain 2 (Task
  Statement 2.4), applying the whole module to one production rollout.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
