# Path-specific rules for conditional conventions — exercise

`.claude/rules/` files can carry a `paths:` glob list so a rule only loads when
Claude works with matching files. You're given a pure-logic model of that
activation in `starter/rule_matcher.py` — no Claude Code process, no API. You
implement the glob matching and the activation decision; the tests encode the
contract (straight from the documented glob table and loading rules).

## Setup

```bash
cd ~/learn-claude-work/5.2
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## Your task

Implement two functions in `starter/rule_matcher.py`:

1. **`glob_match(pattern, path)`** — gitignore-style matching, exactly what the
   `paths:` field uses:
   - `*` matches within a single segment (never crosses `/`),
   - `**` matches zero or more whole segments,
   - the whole path must match the whole pattern.

2. **`active_rules(path, rules)`** — given the file Claude is working on and a list
   of `{"name", "paths"}` rule dicts, return the names of the **active** rules,
   in input order: a rule with no `paths` is **unconditional** (always active); a
   rule with a `paths` list is active iff **any** of its globs matches `path`.

This models `.claude/rules/` loading: rules without `paths` load globally, while
path-scoped rules activate only for matching files — the core of conditional
convention loading.

## What we check

See `rubric.yaml`: correct `*` vs `**` semantics (no leaking across segments),
unconditional-vs-path-scoped activation, any-glob-matches, order preserved, and the
full suite passing.

## When you're done

Run `pytest` until green, then `/verify 5.2`.
