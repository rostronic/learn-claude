# Iterative refinement techniques — exercise

You're given a pure-logic model of two refinement decisions in `starter/refine.py`:
the verify-driven iteration rule and the context-hygiene decision. No Claude Code
process, no API — you implement the documented rules; the tests encode the contract.

## Setup

```bash
cd ~/learn-claude-work/5.6
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## Your task

Implement two functions in `starter/refine.py`:

1. **`should_keep_iterating(check_passed, attempts, max_attempts)`** — keep iterating
   **iff** the check has not passed **and** you're under the cap. The check passing
   is the real stop signal; the cap is only a runaway guard.

2. **`next_context_action(same_issue_corrections, switching_to_unrelated_task)`** —
   return `"clear"` when switching to an unrelated task, or after **more than two**
   corrections on the same issue; otherwise `"continue"`.

## What we check

See `rubric.yaml`: iteration stops on the check (not on the cap when the check
already passed), the cap still prevents spinning forever, and the context action
matches the documented reset rules. The full suite must pass.

## When you're done

Run `pytest` until green, then `/verify 5.6`.
