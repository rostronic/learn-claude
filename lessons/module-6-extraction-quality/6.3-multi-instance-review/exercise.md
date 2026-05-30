# Multi-instance & multi-pass review architectures — exercise

## What you're building

Three functions in `review_architecture.py` that implement the review architecture from the lesson: an **independent** reviewer (fresh context, no generation reasoning), a **multi-pass** reviewer (per-file passes + one integration pass), and **confidence-calibrated routing** of findings.

## Functions to implement

```python
def independent_review(client, code, review_tool) -> list
    # A FRESH single-turn review of `code` only — no generator context threaded in.
    # Forces review_tool; returns the findings list.

def multi_pass_review(client, files, review_tool) -> list
    # files: dict of path -> contents. One focused pass per file (local issues)
    # PLUS one integration pass over all files (cross-file data flow).
    # Returns the combined findings. Total passes == len(files) + 1.

def route_by_confidence(findings, threshold=0.8) -> dict
    # {"auto": [...], "human_review": [...]} split on each finding's "confidence".
```

`REVIEW_TOOL` is provided in `review.py`, and a `_review_pass` helper is already in `review_architecture.py` — use it.

## Requirements

You must:

1. **Make the reviewer independent.** `independent_review` builds a fresh `messages` list containing only the review instruction and the code. It must NOT thread in the generator's conversation or reasoning. Force `review_tool` and return its `findings`.
2. **Split large reviews into passes.** `multi_pass_review` runs one focused pass per file (each seeing only that file), then one integration pass over all files together. Total model calls = `len(files) + 1`. Return all findings combined.
3. **Route by self-reported confidence.** `route_by_confidence` returns `{"auto": [...], "human_review": [...]}`, sending a finding to `"auto"` iff its `confidence >= threshold`.
4. **Pass every test in `test_review_architecture.py`.**

You must NOT:

5. **Perform self-review by passing the generator's context into the reviewer.** The reviewer must not receive prior assistant turns / the generation transcript — independence is the whole point, and the rubric checks for it (`check: anti_pattern`).
6. **Collapse a multi-file review into a single combined pass.** Reviewing all files in one model call is the attention-dilution anti-pattern; you must run per-file passes plus a separate integration pass.

## How to run it

```bash
cd ~/learn-claude-work/6.3
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests mock the Anthropic client — no `ANTHROPIC_API_KEY` needed, no credits burned. After the tests pass you can set `ANTHROPIC_API_KEY` and run `python review_architecture.py` to review a tiny snippet against the real API.

When you're ready (or stuck), run `/verify 6.3` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — subagents run in their own context window, the mechanism behind an independent reviewer.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — forcing a findings tool so each pass returns structured findings.
