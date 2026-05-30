# Context in large codebase exploration — exercise

## What you're building

Implement the three exploration helpers in `exploration.py`. Together they are the deterministic core of context-efficient exploration from the lesson: find the relevant files (search-first), order them so the key file isn't buried (position-aware), and cap verbose tool output before it floods the window.

You'll work against `fixtures.py`, a fully implemented fake repo index of 10 files across several subsystems (auth, billing, search, ratelimit, ui, notifications). Don't edit it — it's the repo you're exploring.

## Function signatures

```python
def select_files(query, index, max_files=5):
    """
    Search-first file selection.

    Args:
        query:     str — what the agent is looking for (e.g. "user login and session").
        index:     list[dict] — repo index entries, each {"path": str, "summary": str}.
        max_files: int — the cap on how many paths to return.

    Returns:
        list[str] — at most max_files paths, ranked by keyword overlap between the
        query and each entry's path+summary, most-relevant first. A SUBSET of the
        index — never all entries when more exist.
    """


def trim_output(text, max_lines=50):
    """
    Cap verbose tool output and mark the truncation.

    Args:
        text:      str — possibly long tool output (e.g. a file read or directory listing).
        max_lines: int — the maximum number of lines to keep.

    Returns:
        str — text unchanged if it has <= max_lines lines; otherwise the first
        max_lines lines followed by a marker like "... [truncated N lines]".
    """


def order_by_relevance(chunks):
    """
    Position-aware ordering.

    Args:
        chunks: list[dict] — each {"path": str, "score": number}.

    Returns:
        list[dict] — the same chunks ordered by "score" descending (highest first).
    """
```

## Requirements

You must:

1. **`select_files` ranks by keyword overlap and returns a subset.** Tokenize the query and each entry's `path + summary`, count overlapping terms, and return the top `max_files` paths in descending-overlap order. With a 10-entry index and `max_files=5`, you return at most 5 — never all 10.
2. **`select_files` puts the most relevant path first.** Highest overlap leads.
3. **`trim_output` leaves short text alone, caps long text, and marks the cut.** If `len(lines) <= max_lines`, return `text` unchanged. Otherwise keep the first `max_lines` lines and append a truncation marker that reports how many lines were dropped.
4. **`order_by_relevance` sorts by `score` descending** and keeps every chunk.
5. **Pass every test in `test_exploration.py`.**

You must NOT:

6. **Return the whole index from `select_files`.** Returning every entry (or ignoring `max_files`) defeats search-first — it's the read-everything anti-pattern the lesson warns about, and it's graded directly (`check: anti_pattern`).
7. **Return verbose output untrimmed from `trim_output`.** Long text must be capped and marked; passing it through whole is the second graded anti-pattern.

The verifier reads your code for these two anti-patterns. They fail the rubric whether or not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/7.2
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — no Anthropic API, no network, no `ANTHROPIC_API_KEY`. In a real session these helpers would run *inside a subagent* so even the index scan and trimmed reads stay out of the parent's context (lesson, "Delegate exploration to a subagent"); here you build the deterministic core.

When you're ready (or stuck), run `/verify 7.2` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Claude Code — Common workflows](https://code.claude.com/docs/en/common-workflows) — the "find relevant code" and "delegate research to subagents" recipes behind search-first and delegation.
- [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows) — progressive token accumulation and context rot: why ordering and trimming matter.
