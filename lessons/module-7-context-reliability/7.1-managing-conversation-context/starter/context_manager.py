"""Client-side conversation context manager.

Implement ``manage_context`` so a long, growing conversation stays under a token
budget without losing critical information — the idea behind server-side
compaction, done client-side. See lesson.md (chapter 7.1) for the principles.
"""

from typing import Callable, Dict, List


def manage_context(messages, token_budget, summarizer, keep_recent=4):
    """Shrink an over-budget conversation by summarizing its stale middle.

    Args:
        messages:     list[dict], each {"role": str, "content": str, "tokens": int}.
                      The FIRST message with role "system" is pinned and must
                      always survive, verbatim, at the head of the result.
        token_budget: int. If the conversation's total ``tokens`` is at or below
                      this, return it UNCHANGED (don't pay to summarize).
        summarizer:   callable(list[dict]) -> str. Collapses a list of messages
                      into a single summary string. (In production a Claude call;
                      in tests a deterministic stub.)
        keep_recent:  int. The most recent ``keep_recent`` non-system turns are
                      kept verbatim at the tail.

    Returns:
        A new messages list. When over budget: [system, summary, *recent], where
        the summary of the OLDER middle messages is placed immediately AFTER the
        system message (the high-attention head) — never appended at the end and
        never buried in the middle. Every message keeps an int ``tokens``;
        estimate the summary's as ``len(summary) // 4`` (min 1).

    Steps:
      1. Find the first "system" message; set it aside as the pin. The rest is
         the body.
      2. If total tokens <= token_budget, return the messages unchanged.
      3. Split the body into the recent tail (last keep_recent) and the stale
         middle (everything before it).
      4. If the middle is empty, there's nothing old to summarize — return as-is.
      5. Call summarizer(middle) -> str; wrap it in ONE message with an int
         tokens estimate.
      6. Reassemble and return [system, summary, *recent] — summary at the head,
         right behind the pinned system message. Never drop the system message;
         never naively truncate.
    """
    # TODO: implement the steps above.
    raise NotImplementedError("Implement manage_context (see steps in the docstring).")
