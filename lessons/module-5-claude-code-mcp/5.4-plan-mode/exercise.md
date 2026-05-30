# Plan mode vs direct execution — exercise

You're given a pure-logic model of the plan-mode decision in
`starter/plan_decision.py`. No Claude Code process, no API — you implement the
documented heuristic and the rule for what plan mode permits; the tests encode the
contract.

## Setup

```bash
cd ~/learn-claude-work/5.4
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## Your task

Implement two functions in `starter/plan_decision.py`:

1. **`should_use_plan_mode(task)`** — return `True` when **any** documented trigger
   holds: `approach_uncertain`, `files_touched > 1`, or `unfamiliar_code`. Otherwise
   (clear scope, single file, familiar — a one-sentence diff) return `False` to act
   directly.

2. **`plan_mode_allows(is_mutating)`** — plan mode is read/analyze-only: return
   `True` for a non-mutating action, `False` for a mutating one (edit/write).

## What we check

See `rubric.yaml`: the decision matches the documented triggers (and a
one-sentence-diff task is NOT over-planned), plan mode allows reads but blocks edits,
and the full suite passes.

## When you're done

Run `pytest` until green, then `/verify 5.4`.
