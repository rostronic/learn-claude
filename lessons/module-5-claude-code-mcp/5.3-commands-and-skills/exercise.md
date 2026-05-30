# Custom slash commands and skills — exercise

You're given a pure-logic model of two skill behaviors in
`starter/skill_invoke.py`: expanding argument placeholders in a skill body, and
deciding who may invoke a skill from its frontmatter flags. No Claude Code process,
no API — you implement the rules from the skills docs; the tests encode the
contract.

## Setup

```bash
cd ~/learn-claude-work/5.3
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## Your task

Implement two functions in `starter/skill_invoke.py`:

1. **`expand_arguments(body, args)`** — replace `$ARGUMENTS` with all args joined by
   a space, and `$1`..`$9` with the matching positional arg (or `""` if out of
   range). Leave other text — including a bare `$` and `$0` — untouched.

2. **`can_invoke(skill, actor)`** — given a skill's frontmatter flags
   (`disable_model_invocation`, default `False`; `user_invocable`, default `True`)
   and an `actor` of `"user"` or `"model"`, return whether that actor may invoke
   the skill. Default: both. `disable_model_invocation: true` → user only.
   `user_invocable: false` → model only.

This is the invocation-control logic the exam leans on: a side-effecting workflow
like `/deploy` sets `disable_model_invocation: true` so Claude can't trigger it on
its own.

## What we check

See `rubric.yaml`: correct placeholder expansion (no `$0`/bare-`$` mangling),
correct invocation matrix, and the full suite passing.

## When you're done

Run `pytest` until green, then `/verify 5.3`.
