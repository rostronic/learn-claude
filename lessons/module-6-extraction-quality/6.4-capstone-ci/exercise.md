# Capstone — Claude Code for Continuous Integration — exercise

## What you're building

A compact CI code-review pipeline in `ci_review.py` that integrates the whole module: build a headless Claude Code invocation, route jobs to sync vs batch, review a PR with independent multi-pass review filtered to explicit criteria, and format actionable PR comments. Everything runs against pure data or a mocked Anthropic client — no real API calls.

## Functions to implement

```python
def claude_ci_command(prompt, allowed_tools, output_format="json") -> list   # CCAF 3.6
    # argv for a NON-INTERACTIVE Claude Code run: -p, --allowedTools (scoped),
    # --output-format. Never disables permission checks.

def route_review_job(job) -> str                                             # CCAF 4.5
    # "sync" for a blocking job, "batch" for a latency-tolerant one.

def review_pull_request(client, files, report_categories, review_tool=REVIEW_TOOL) -> list
    # Independent multi-pass review (per-file + integration), filtered to the    # CCAF 4.6 + 4.1
    # in-scope report_categories.

def format_pr_feedback(findings) -> list[str]
    # "<file>:<line> [<severity>] <issue>" comment lines (omit :line if absent).
```

`REVIEW_TOOL` and the `_review_pass` helper are already provided in `ci_review.py`.

## Requirements

You must:

1. **Run headless (3.6).** `claude_ci_command` returns argv containing `-p`, the prompt, `--allowedTools` with the comma-joined tools, and `--output-format`. The tool scope must be exactly what's passed in.
2. **Route by latency (4.5).** `route_review_job` returns `"sync"` for blocking jobs and `"batch"` otherwise.
3. **Review independently and multi-pass (4.6).** `review_pull_request` runs one focused pass per file plus one integration pass (`len(files) + 1` model calls), each a fresh independent instance (no generation context).
4. **Filter to explicit criteria (4.1).** Keep only findings whose `category` is in `report_categories`; drop the rest.
5. **Format actionable comments.** `format_pr_feedback` renders each finding as `file:line [severity] issue` (omit `:line` when a finding has no line).
6. **Pass every test in `test_ci_review.py`.**

You must NOT:

7. **Disable permission checks wholesale.** `claude_ci_command` must never emit a "skip all permissions" flag (e.g. anything containing `dangerously`); scope tools with `--allowedTools` instead. Checked directly by the rubric (`check: anti_pattern`).
8. **Route a blocking pre-merge check to batch.** A blocking job has a latency requirement the batch API (no SLA, up-to-24-hour window) can't meet. Also checked by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/6.4
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests mock the Anthropic client — no `ANTHROPIC_API_KEY` needed, no credits burned.

When you're ready (or stuck), run `/verify 6.4` and I'll grade you. This is the module capstone — if a piece feels unfamiliar, revisit 6.1–6.3 (and 6.2 for the sync/batch call).

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Run Claude Code programmatically (headless)](https://code.claude.com/docs/en/headless) — `-p`, `--allowedTools`, `--output-format`.
- [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) — the sync-vs-batch decision.
- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — independent reviewer instances.
