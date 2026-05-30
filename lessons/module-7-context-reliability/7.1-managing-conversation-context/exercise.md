# Managing conversation context across long interactions — exercise

## What you're building

Implement `manage_context` in `context_manager.py`. It's the client-side compactor from the lesson: keep the pinned system prompt and the most recent turns verbatim, and — only when the conversation is over budget — collapse the stale middle into a single summary placed right behind the system prompt.

## Function signature

```python
def manage_context(messages, token_budget, summarizer, keep_recent=4):
    """
    Args:
        messages:     list[dict], each {"role", "content", "tokens": int}.
                      The first 'system' message is pinned and must always survive.
        token_budget: int — if total tokens <= budget, return messages unchanged.
        summarizer:   callable(list[dict]) -> str — collapses messages into one summary.
        keep_recent:  int — the most recent non-system turns kept verbatim (default 4).

    Returns:
        A new messages list. Over budget: [system, summary, *recent], summary placed
        immediately after the system message. Each message keeps an int 'tokens';
        estimate the summary's as len(summary) // 4 (min 1).
    """
```

Use the deterministic `fake_summarizer` and `sample_conversation()` from `fixtures.py` — they're fully implemented; don't edit them.

## Requirements

You must:

1. **Always preserve the pinned system message** (the first message with role `"system"`), verbatim, as the first message of the result.
2. **Keep the most recent `keep_recent` non-system turns verbatim** at the tail.
3. **When the conversation is over budget, summarize the older middle messages into a SINGLE summary message** via `summarizer(middle)`, and place it immediately **after** the system message — not at the end, not buried in the middle.
4. **Return the conversation unchanged when it's already at or under budget** — don't pay to summarize what already fits.
5. **Keep the result's total `tokens` at or below `token_budget`**, and give every message an integer `tokens` value.
6. **Pass every test in `test_context_manager.py`.**

You must NOT:

7. **Naively truncate or drop messages without summarizing**, and **never drop the system message.** No `messages = messages[-N:]` sliding window that discards old context — Task Statement 5.1 is about *preserving* critical information. Compress the middle into a summary; never delete it, and never evict or summarize the system prompt.

Requirement 7 is graded directly by the rubric (`check: anti_pattern`). The verifier reads your code for it; it fails the rubric whether or not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/7.1
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic with a deterministic fake summarizer — no `ANTHROPIC_API_KEY` and no network needed.

When you're ready (or stuck), run `/verify 7.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) — the server-side progressive summarization your `manage_context` reimplements client-side.
- [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) — `count_tokens` for measuring input size before you send.
