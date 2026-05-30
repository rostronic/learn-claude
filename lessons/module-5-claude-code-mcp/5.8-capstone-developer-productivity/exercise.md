# Capstone — Developer Productivity with Claude — exercise

This capstone is a **design/analysis** exercise, not an API task. You encode the
requirement → mechanism mapping from the lesson as a checkable rollout plan, and a
validator confirms each platform-team requirement is met with the
Anthropic-prescribed mechanism — and that none of the module's anti-patterns slipped
in. No Claude Code process, no API.

## Setup

```bash
cd ~/learn-claude-work/5.8
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## The scenario

A platform team is rolling Claude Code out to 60 engineers across a monorepo (the
lesson's running scenario). Six requirements, each with one correct mechanism:

| Requirement key | Correct mechanism |
|---|---|
| `repo_conventions` | project `./CLAUDE.md` |
| `language_rules` | path-scoped rule (`.claude/rules/` + non-empty `paths`) |
| `no_edit_generated` | blocking `PreToolUse` hook |
| `deploy_workflow` | skill with `disable_model_invocation: true` |
| `shared_database` | project-scope MCP, secret **not** in the file |
| `ci_review` | GitHub Action with a `${{ secrets.* }}` api key |

## Your task

Implement **`validate_plan(plan)`** in `starter/rollout_plan.py`. Given a plan dict
mapping each requirement key to a chosen mechanism, return a list of problem strings
(empty list = valid). Each problem string must contain the offending requirement key.
Flag the documented anti-patterns: conventions in the wrong scope, language rules
without path scoping, the no-edit rule as a prompt instead of a blocking hook, a
model-invocable deploy skill, a non-shared or secret-leaking database server, a
hard-coded CI key, and any missing requirement.

The full docstring in `starter/rollout_plan.py` specifies the exact shape of each
mechanism dict.

## What we check

See `rubric.yaml`: a correct plan yields no problems, each anti-pattern is flagged by
its requirement key, missing requirements are caught, and the full suite passes.

## When you're done

Run `pytest` until green, then `/verify 5.8`. That completes Module 5 — consider a
`/mock-exam CCAF` run to see how the whole module holds up.
