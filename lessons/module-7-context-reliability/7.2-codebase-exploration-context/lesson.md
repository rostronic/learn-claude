---
chapter: "7.2"
slug: "codebase-exploration-context"
title: "Context in large codebase exploration"
module: "module-7-context-reliability"
sequence: 29
references:
  - title: "Claude Code — Common workflows"
    url: "https://code.claude.com/docs/en/common-workflows"
    type: official_docs
    covers: "Understand new codebases, find relevant code, delegate research to subagents"
  - title: "Agent SDK — Subagents"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Fresh context window per subagent; only the final message returns to the parent"
  - title: "Claude Code — Working with large codebases"
    url: "https://code.claude.com/docs/en/large-codebases"
    type: official_docs
    covers: "Configuring Claude Code for monorepos and very large repositories"
  - title: "Context windows"
    url: "https://platform.claude.com/docs/en/build-with-claude/context-windows"
    type: official_docs
    covers: "Progressive token accumulation and context rot as the window fills"
  - title: "Context editing"
    url: "https://platform.claude.com/docs/en/build-with-claude/context-editing"
    type: official_docs
    covers: "Tool-result clearing; irrelevant content degrades model focus"
---

# Context in large codebase exploration

## Overview

A 200k-token context window sounds like a lot until you point an agent at a real repository. A single mid-sized service can be hundreds of files and millions of tokens; "read the codebase, then fix the bug" is not a plan, it's an overflow. Task Statement 5.4 is about the discipline that makes exploration scale: **manage context effectively in large codebase exploration** — get the agent to the few files that matter without dragging the whole tree into the window.

The reason this is its own task statement (and not just "be efficient") is that context isn't free or neutral. Two facts from the platform docs drive everything in this lesson:

- **Tokens accumulate progressively.** Every file read, every tool result, every directory listing stays in the conversation and counts against the window — "Progressive token accumulation: As the conversation advances through turns, each user message and assistant response accumulates within the context window," which the docs describe as the model's "working memory" ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)).
- **A full window is a *worse* window, not just a fuller one.** Accuracy degrades as the window fills — the docs call this **context rot** — and "irrelevant content degrades model focus" ([Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)). Reading 50 files to find the 2 that matter doesn't just cost tokens; it buries the 2 that matter under 48 that don't.

So the goal isn't "fit the repo in the window." It's the opposite: **keep the window small and high-signal.** Four techniques get you there, and this lesson teaches all four — search-first retrieval, trimming verbose tool output, position-aware ordering, and delegating exploration to subagents.

## How it works

### Search-first: find the files, don't read the repo

The first move on any unfamiliar codebase is *not* to read it top to bottom. Claude Code's own guidance for "find relevant code" is to ask for the files that handle a concern — "find the files that handle user authentication" — and let the agent use `Grep`/`Glob`/search to locate them ([Common workflows](https://code.claude.com/docs/en/common-workflows)). You start broad ("give me an overview of this codebase") and then **narrow to the subsystem** before any file gets fully read.

The mechanism is cheap: a grep over the tree returns paths and matching lines — kilobytes — instead of the full contents of every candidate file. You spend a tiny amount of context to *decide* what's worth spending real context on. Reading a file should be a deliberate act that follows a search, not the search itself.

In code, search-first is a ranking-then-select step over an index of the repo (paths plus short summaries), returning only the top matches:

```python
def select_files(query, index, max_files=5):
    """Rank index entries by keyword overlap with the query; return the top paths."""
    query_terms = set(_tokenize(query))   # _tokenize lowercases and drops stopwords
    scored = []
    for entry in index:
        haystack = _tokenize(entry["path"] + " " + entry["summary"])
        overlap = sum(1 for t in haystack if t in query_terms)
        if overlap > 0:
            scored.append((overlap, entry["path"]))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [path for _score, path in scored[:max_files]]
```

The load-bearing detail is `max_files`: even when the index has 40 plausible entries, you return at most a handful. Selecting a **subset** is the entire point — if you return everything, you haven't searched, you've just deferred the overflow.

### Trim verbose tool output

Tools that explore — `ls -R`, a full-file `Read`, a test runner — emit a lot. A recursive directory listing of a monorepo, or a 4,000-line generated file, is mostly noise, and all of it accumulates in the window. The fix is to **cap output and mark the truncation** so neither you nor the model pretends the full thing is present:

```python
def trim_output(text, max_lines=50):
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    kept = lines[:max_lines]
    dropped = len(lines) - max_lines
    return "\n".join(kept) + "\n... [truncated {} lines]".format(dropped)
```

The marker matters as much as the cap. A silent truncation invites the model to reason as if it saw the whole file; an explicit `... [truncated N lines]` tells it the view is partial, so it can ask for more if it needs to. This is the same instinct the platform formalizes as **tool-result clearing** in context editing — old, bulky tool results get cleared because "context is a finite resource with diminishing returns, and irrelevant content degrades model focus" ([Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)). Trimming caps the result on the way in; clearing removes stale results that already landed. Both keep the window high-signal.

### Position-aware ordering: put the key file first

Where context sits in the window changes how well the model uses it. Because accuracy degrades as the window fills — context rot ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)) — the *most* relevant material should be the *least* buried. After you've scored your candidate chunks, order them so the highest-signal file leads:

```python
def order_by_relevance(chunks):
    """chunks: list of {path, score}. Return them sorted highest score first."""
    return sorted(chunks, key=lambda c: c["score"], reverse=True)
```

This is a small function with a large rationale. If your retrieval surfaces the right file but drops it at the bottom of a long context dump, you've paid the token cost and still risk the model anchoring on the noise above it. Rank, then present in rank order.

### Delegate exploration to a subagent

The most powerful technique is to not bring the exploration into your context at all. A subagent runs in **its own fresh context window**; "intermediate tool calls and results stay inside the subagent; only its final message returns to the parent" ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Claude Code's workflow guidance is explicit about why this matters here: "Exploring a large codebase fills your context with file reads. Delegate the exploration so only the findings come back" ([Common workflows](https://code.claude.com/docs/en/common-workflows)).

So the parent says "find where rate limiting is enforced and summarize the call path"; the subagent greps, reads ten files, follows imports, and burns all of that in its *own* window — then returns three sentences and two file paths. The parent's context grows by a paragraph, not by ten files. This is **context isolation**, and it's the prescribed pattern for any open-ended "go understand X" task in a big repo. One constraint to remember: the only parent→child channel is the prompt string you hand the subagent, so pass the file paths, the concern, and any constraints explicitly — the subagent does not inherit your conversation ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).

For genuinely large repos, Claude Code is also configurable for the scale itself — monorepo layout, what to index, what to ignore ([Working with large codebases](https://code.claude.com/docs/en/large-codebases)) — but configuration is a complement to the four techniques above, not a substitute for them.

## Worked example

Put the pieces together into the exploration pipeline the exercise builds. Given a query and a repo index, you select a handful of files (search-first), order them by relevance (position-aware), and trim any verbose output before it enters the window:

```python
REPO_INDEX = [
    {"path": "auth/login.py",        "summary": "user login and session creation"},
    {"path": "auth/tokens.py",       "summary": "JWT token issue and refresh"},
    {"path": "billing/invoice.py",   "summary": "invoice generation and totals"},
    {"path": "search/indexer.py",    "summary": "full text search indexing"},
    {"path": "ratelimit/limiter.py", "summary": "request rate limiting middleware"},
    {"path": "ui/dashboard.py",      "summary": "dashboard rendering"},
    # ... several more across subsystems
]

# 1. Search-first: get the few files that match, not the whole index.
paths = select_files("how is user login and session handled", REPO_INDEX, max_files=3)
# -> ["auth/login.py", "auth/tokens.py", ...]  (a SUBSET, ranked by overlap)

# 2. Position-aware: order the candidate chunks so the key file leads.
chunks = [
    {"path": "auth/login.py",  "score": 9},
    {"path": "auth/tokens.py", "score": 6},
    {"path": "ui/dashboard.py","score": 1},
]
ordered = order_by_relevance(chunks)
# -> login.py (9), tokens.py (6), dashboard.py (1)

# 3. Trim: cap a verbose read before it bloats the window.
raw = open_file_contents("auth/login.py")          # say, 800 lines
view = trim_output(raw, max_lines=50)
# -> first 50 lines + "\n... [truncated 750 lines]"
```

Walking through it:

- **`select_files` returns a subset.** With six-plus entries in the index and `max_files=3`, you get back at most three paths, ranked by keyword overlap, and the obviously irrelevant ones (`billing/invoice.py`, `search/indexer.py`) never enter the picture. That's the search-first contract: spend a little context to choose, don't read everything.
- **`order_by_relevance` is stable and descending.** The highest-scoring file is first so it isn't buried — directly countering context rot.
- **`trim_output` caps *and* announces.** Fifty lines kept, a `... [truncated 750 lines]` marker appended, so downstream reasoning knows the view is partial.

In a real Claude Code session, steps 1–3 would themselves run inside a subagent so that even the index scan and the trimmed reads stay out of the parent's window, and only the final answer ("login is in `auth/login.py`, sessions are created at line 42…") comes back. The exercise implements the deterministic core; the subagent wrapper is the production framing.

## Anti-patterns & pitfalls

This task statement is defined by the wrong moves as much as the right ones. Each of these is a tempting distractor:

1. **Reading the whole repo (or the whole directory) into context "to be safe."** The instinct that more context is safer is exactly backwards. Tokens accumulate ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)), and a window full of irrelevant files degrades focus ([Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)). The prescribed move is **search-first** — locate the relevant files with grep/glob, then read only those ([Common workflows](https://code.claude.com/docs/en/common-workflows)). A `select_files` that returns the entire index has failed the exercise on purpose: returning everything is the anti-pattern.
2. **Dumping verbose tool output verbatim.** Piping a recursive listing or an 800-line file straight into the conversation, untrimmed, is how a single tool call eats a third of your window. Cap it and mark the truncation. Untrimmed verbose output is the second graded anti-pattern.
3. **Ignoring position — burying the key file.** Retrieving the right file but presenting it last, under a pile of lower-relevance context, wastes the retrieval. Context rot is real ([Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)); order most-relevant-first.
4. **Exploring directly in the main agent's context.** Doing the dozen grep-and-read steps inline means the parent window absorbs all of it. The Anthropic-prescribed pattern for open-ended exploration is to **delegate to a subagent** so only the findings return ([Subagents](https://code.claude.com/docs/en/agent-sdk/subagents), [Common workflows](https://code.claude.com/docs/en/common-workflows)). "Just read more, the window is big" is not a strategy — it's the failure mode the strategy exists to prevent.

The through-line: a bigger window is not a license to fill it. Every technique here trades a little selection effort for a lot of preserved signal, and on this exam the selective approach is the correct one — the read-everything alternatives are wrong, not merely slower.

## Exam focus

Task Statement 5.4 lives in Domain 5 and shows up wherever an agent has to operate over a body of code or documents it didn't write:

- **Developer-productivity scenarios** — "understand this service and fix the bug" questions hinge on whether you search-first and delegate, or read the tree.
- **Multi-agent / research scenarios** — the coordinator that farms exploration out to subagents and keeps only findings is the right answer; the one that reads everything itself is the distractor.

Expect distractors that frame reading the whole repo as "thorough," dumping full tool output as "complete," or doing exploration inline as "simpler." The correct answer is always the one that keeps the parent context small and high-signal: search-first, trim, order by relevance, delegate.

## References & further reading

- [Claude Code — Common workflows](https://code.claude.com/docs/en/common-workflows) — the "find relevant code" and "delegate research to subagents" recipes; the practical source for search-first and exploration delegation.
- [Agent SDK — Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) — fresh context window per subagent and the rule that only the final message returns to the parent (context isolation), plus what a subagent does and does not inherit.
- [Claude Code — Working with large codebases](https://code.claude.com/docs/en/large-codebases) — configuring Claude Code for monorepos and very large repos when scale itself is the problem.
- [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows) — progressive token accumulation and context rot: why a full window is a worse window.
- [Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) — tool-result clearing and the principle that irrelevant content degrades model focus.

## Exam coverage

- **CCAF** — Domain 5 (Context Management & Reliability), Task Statement 5.4: Manage context effectively in large codebase exploration.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
