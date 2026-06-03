---
chapter: "7.1"
slug: "managing-conversation-context"
title: "Managing conversation context across long interactions"
module: "module-7-context-reliability"
sequence: 28
references:
  - title: "Context windows"
    url: "https://platform.claude.com/docs/en/build-with-claude/context-windows"
    type: official_docs
    covers: "Progressive token accumulation, context rot, context awareness, overflow behavior"
  - title: "Compaction"
    url: "https://platform.claude.com/docs/en/build-with-claude/compaction"
    type: official_docs
    covers: "Server-side progressive summarization of older context near the limit"
  - title: "Context editing"
    url: "https://platform.claude.com/docs/en/build-with-claude/context-editing"
    type: official_docs
    covers: "Fine-grained curation; irrelevant content degrades focus"
  - title: "Token counting"
    url: "https://platform.claude.com/docs/en/build-with-claude/token-counting"
    type: official_docs
    covers: "count_tokens to estimate input size before sending"
  - title: "Memory tool"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool"
    type: official_docs
    covers: "Scratchpad files in /memories; the multi-session recovery pattern"
---

# Managing conversation context across long interactions

## Overview

A long-running interaction — a multi-turn support session, an agent grinding through a refactor, a research run that reads dozens of files — has a structural problem: the conversation only grows. Every turn appends the assistant's reply and any tool results to the history you send back: as the docs put it, "Progressive token accumulation: As the conversation advances through turns, each user message and assistant response accumulates within the context window." ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). Left alone, that accumulation does two bad things: it eventually overflows the window, and — well before that — it *degrades the model's accuracy*. Managing context is the discipline of keeping the window focused on what matters while the interaction outlives any single window's worth of tokens.

This is Domain 5, Task Statement 5.1: **manage conversation context to preserve critical information across long interactions**. The verb is *preserve* — the failure mode isn't just overflow, it's losing the one fact (the customer's account ID, the design constraint agreed ten turns ago) that the rest of the task depends on. A naive truncation that drops old messages to fit the window will happily throw that fact away. The whole job is to shrink the token footprint *without* losing the load-bearing information.

Anthropic gives you a layered toolkit for this — token counting to *measure* before you send, server-side compaction and client-side context editing to *shrink* automatically, and the memory tool to *persist* critical state outside the window entirely. This lesson teaches the principles those tools embody, then has you build the core move by hand: a context manager that summarizes the stale middle of a conversation while pinning the system prompt and the most recent turns verbatim.

## How it works

### Measure first: count tokens before you send

You can't manage a budget you can't see. The Messages API exposes `client.messages.count_tokens(...)`, which "returns the number of tokens that would be used by a request" as `{ "input_tokens": N }` ([Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)). It takes the same `model`, `system`, `messages`, and `tools` shape as `messages.create`, so you can price a request *before* spending on it:

```python
import anthropic

client = anthropic.Anthropic()

count = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a support agent.",
    messages=conversation,
)
print(count.input_tokens)   # e.g. 48213
```

Two caveats the docs are explicit about. The count is an **estimate** — "The token count should be considered an estimate. In some cases, the actual number of input tokens used when creating a message may differ by a small amount." ([Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)) — so budget with headroom, never to the byte. And the prescribed pattern is to use this measurement to *decide*: if the projected input is near your budget, compact before sending rather than discovering the problem when the API rejects an over-window request with `stop_reason: "model_context_window_exceeded"` ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). Measuring beats hoping the model "remembers" or that you'll happen to stay under the limit.

### Why accumulation hurts: context rot

The window has a hard ceiling, but the more important effect kicks in long before that. As the token count climbs, the model's ability to use any one piece of context reliably drops — Anthropic calls this **context rot**: "As token count grows, accuracy and recall degrade, a phenomenon known as context rot." ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). Context editing's framing is blunter: "context is a finite resource with diminishing returns, and irrelevant content degrades model focus" ([Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)).

The takeaway flips a common intuition: a bigger window is not a license to dump everything in. Stuffing the history with stale tool outputs and superseded turns doesn't just risk overflow — it actively makes the model worse at the turns that remain. The goal is a *small, relevant* context, not a *full* one.

### Shrink automatically: compaction and context editing

Anthropic ships two server-side / SDK mechanisms that act on this principle:

- **Compaction** does progressive summarization for you. As the conversation approaches the limit, it "keeps the active context focused and performant by replacing stale content with concise summaries" ([Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)). It triggers automatically near a configurable threshold (default 150k input tokens, minimum 50k). The summary replaces the older raw turns; recent turns and the system prompt stay intact.
- **Context editing** is finer-grained curation: clearing stale **tool results** and **thinking blocks** from the history so the bytes they occupied are reclaimed without summarizing whole turns ([Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)).

The exercise has you implement the *idea* behind compaction yourself — progressive summarization with a pinned head and tail — because understanding the move is what the exam tests, and because you'll often want the same logic client-side before a request ever leaves your process.

### Lost in the middle: where you put the summary matters

There's a placement subtlety that trips people up. When you collapse old turns into a summary, *where* in the message list you put that summary changes how reliably the model uses it. Models attend most strongly to the **start and end** of the context and least to the buried middle — the "lost in the middle" effect. So the layout that survives context rot best is:

1. **System prompt — pinned at the very top.** It carries the standing instructions; it must never be summarized away or dropped.
2. **The summary of older turns — placed immediately after the system prompt**, at the *head* of the conversation, not buried in the middle and not appended at the end where it would push the recent turns away from the edge.
3. **The most recent turns — verbatim, at the tail**, where the model attends to them most and where the immediate task lives.

Critical, durable information lives at the edges (system prompt at the head, live task at the tail); the compressed history sits right behind the system prompt so it stays near the high-attention front of the window rather than rotting in the middle.

### Persist across sessions: the memory tool

Compaction and editing manage a *single* window. Some information has to outlive the window — and even outlive the whole session. The **memory tool** is Anthropic's mechanism for that: a client-side file directory (conventionally `/memories`) that "Claude can create, read, update, and delete files in" to "store and reference information outside the context window" ([Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)). It's a scratchpad on disk: Claude writes the durable facts to a file, and the bytes no longer ride along in every request.

The doc spells out a **multi-session pattern** for exactly the long-interaction case: an initializer writes a progress log and a checklist to `/memories`; each new session begins by reading those files to "recover state" and resume where the last one stopped, then updates them before ending ([Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)). Memory "persists important information across compaction boundaries" — so when compaction discards the raw turns that recorded a decision, the decision still lives in a memory file. The pairing is the point: compaction keeps the active window lean; memory keeps the critical facts recoverable no matter how aggressively the window is trimmed.

## Worked example

The exercise's `manage_context` is a client-side compactor. You hand it the running conversation, a token budget, and a `summarizer` callable (in production, a Claude call; in tests, a deterministic stub). It pins the system message and the most recent `keep_recent` turns, and — only if the conversation is over budget — collapses the stale middle into one summary placed right behind the system prompt.

```python
def manage_context(messages, token_budget, summarizer, keep_recent=4):
    # 1. Identify the pinned system message (first 'system' role).
    system_idx = next(
        (i for i, m in enumerate(messages) if m["role"] == "system"), None
    )
    system_msg = messages[system_idx] if system_idx is not None else None
    body = [m for i, m in enumerate(messages) if i != system_idx]

    # 2. Under budget? Return unchanged.
    total = sum(m["tokens"] for m in messages)
    if total <= token_budget:
        return list(messages)

    # 3. Split the body into the stale middle and the recent tail.
    recent = body[-keep_recent:] if keep_recent else []
    middle = body[:len(body) - len(recent)]

    # 4. Nothing old enough to summarize -> can't shrink further; return as-is.
    if not middle:
        return list(messages)

    # 5. Collapse the middle into ONE summary message.
    summary_text = summarizer(middle)
    summary_msg = {
        "role": "system",
        "content": summary_text,
        "tokens": max(1, len(summary_text) // 4),
    }

    # 6. Reassemble: system, summary, recent.  Summary sits at the HEAD,
    #    right after the pinned system prompt — never the buried middle.
    out = []
    if system_msg is not None:
        out.append(system_msg)
    out.append(summary_msg)
    out.extend(recent)
    return out
```

Walking through it against a 12-turn conversation that's 3,000 tokens over a budget of 8,000:

- **The system message is found by role and set aside** — it's pinned. Whatever happens to the body, the system prompt is reattached at index 0. It is never a candidate for summarization or dropping.
- **The recent tail is sliced off verbatim.** The last `keep_recent` turns (default 4) are the live task; they pass through untouched, landing at the end of the window where the model attends most.
- **The middle — everything between the system prompt and the recent tail — is the only thing summarized.** One call to `summarizer(middle)` returns a single string; we wrap it in one message and estimate its size as `len(text) // 4`.
- **Placement is deliberate.** The reassembled list is `[system, summary, *recent]` — the summary goes *right after* the system prompt, at the high-attention head, not appended at the tail (which would shove the recent turns toward the middle) and certainly not left buried where the raw turns were.
- **Under-budget input short-circuits at step 2** and is returned unchanged: don't pay to summarize a conversation that already fits.

The result is a much shorter list whose total `tokens` is at or under budget, that still contains the standing instructions, a faithful digest of the history, and the live turns — the three things a long interaction can't lose.

## Anti-patterns & pitfalls

**Naive truncation — dropping the oldest messages to make room.** The tempting one-liner is `messages = messages[-N:]`: keep the last N, discard the rest. It fixes the token count and destroys the task. The "rest" you just deleted contained the pinned system prompt (now gone — the model forgets its instructions) and the load-bearing facts established early in the session (the account ID, the agreed constraint). Task Statement 5.1 is about *preserving* critical information; sliding-window truncation is the canonical way to lose it. The prescribed fix is **summarization, not deletion** — compaction "replac[es] stale content with concise summaries" ([Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)) rather than throwing it away, and the system prompt is never in the discard set. Dropping messages without summarizing is wrong, full stop.

**Dropping or summarizing the system prompt.** A subtler version of the above: a context manager that treats every message uniformly will summarize or evict the system message along with the rest. The standing instructions are not "old context" to be compressed — they're a pin. Always identify the system message and reattach it verbatim at the head.

**Appending the summary at the end (or burying it in the middle).** If you summarize correctly but staple the digest onto the *tail*, you've pushed the recent, live turns away from the high-attention edge and seated the summary in the middle, where the model attends least — straight into the lost-in-the-middle trap. The summary belongs immediately after the system prompt; the recent turns belong at the very end.

**Treating a bigger window as the solution.** "Just use the 200k/1M model and never compact" ignores context rot: "irrelevant content degrades model focus" ([Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)) and, as tokens grow, "As token count grows, accuracy and recall degrade, a phenomenon known as context rot." ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)). A full window is a *worse* window. Manage context regardless of how large the ceiling is.

**Hoping the model "remembers" instead of measuring.** Flying blind — never calling `count_tokens`, never checking projected size, and discovering the overflow only when the API returns `model_context_window_exceeded`. Measure before you send and compact proactively; reactive failure mid-task is the avoidable outcome ([Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)).

## Exam focus

Task Statement 5.1 anchors the Domain 5 questions on keeping long interactions coherent, and it surfaces in any scenario with a session that outruns one window:

- **Customer Support Resolution Agent** — a long troubleshooting thread must not lose the customer's account details or the steps already tried; that's preserve-critical-info under compaction.
- **Multi-Agent Research System** — a research run that reads many sources accumulates tokens fast; compaction plus memory keeps the active window lean while the findings persist.

Expect distractors that *sound* efficient: "truncate to the last N messages," "use the largest context window so you never have to compact," "append a summary at the end," "let it overflow and catch the error." Each is an anti-pattern above. The correct answer always (1) summarizes rather than deletes, (2) pins the system prompt and recent turns, (3) places durable info at the edges, and (4) measures with `count_tokens` / persists with the memory tool rather than hoping.

## References & further reading

- [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows) — how context accumulates every turn, context rot (as token count grows, accuracy and recall degrade), context awareness, and the `model_context_window_exceeded` overflow signal.
- [Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) — server-side progressive summarization that replaces stale content with concise summaries near the limit; the idea the exercise reimplements client-side.
- [Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) — finer-grained curation (clearing stale tool results and thinking blocks) and the "diminishing returns / degrades focus" framing for why a full window is a worse window.
- [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) — `count_tokens` for estimating input size before you send, so you compact proactively instead of overflowing.
- [Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) — the `/memories` scratchpad-file pattern for persisting critical state outside the window, including the multi-session recover-state-and-resume workflow that survives compaction boundaries.

## Exam coverage

- **CCAF** — Domain 5 (Context Management & Reliability), Task Statement 5.1: Manage conversation context to preserve critical information across long interactions.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
