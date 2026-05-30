# Claude Code in CI/CD pipelines — exercise

You're given a pure-logic model of two CI/CD behaviors in `starter/ci_invoke.py`: a
secret-reference check (the #1 CI security rule) and a headless `claude -p` command
builder. No Claude Code process, no API — you implement the rules; the tests encode
the contract.

## Setup

```bash
cd ~/learn-claude-work/5.7
pip install -r requirements.txt && pytest
```

All in-memory; only `pytest` is needed.

## Your task

Implement two functions in `starter/ci_invoke.py`:

1. **`is_secret_reference(value)`** — `True` only for a GitHub Actions secret
   reference like `${{ secrets.NAME }}` (whitespace-tolerant); `False` for a
   hard-coded key or any other expression. This is the rule that keeps API keys out
   of committed workflow files.

2. **`build_headless_command(prompt, ...)`** — build the argv for a non-interactive
   `claude -p` run, appending `--allowedTools` (comma-joined, omitted when empty),
   `--output-format` (only when not the `text` default), and `--permission-mode`
   (when set), in that order.

## What we check

See `rubric.yaml`: a hard-coded key is rejected (only `${{ secrets.* }}` passes), the
command is built with correctly-ordered, conditionally-included flags, and the full
suite passes.

## When you're done

Run `pytest` until green, then `/verify 5.7`.
