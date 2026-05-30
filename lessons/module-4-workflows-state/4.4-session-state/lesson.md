---
chapter: "4.4"
slug: "session-state"
title: "Session state, resumption, and forking"
module: "module-4-workflows-state"
sequence: 15
references:
  - title: "Agent SDK — Work with sessions"
    url: "https://code.claude.com/docs/en/agent-sdk/sessions"
    type: official_docs
    covers: "Session persistence, capturing session_id, continue vs resume vs fork_session, and the cross-host cwd-encoding caveat"
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs
    covers: "Turns, messages, and context accumulation within a single session"
---

# Session state, resumption, and forking

## Overview

A **session** is the conversation history the Agent SDK builds while an agent works — "your prompt, every tool call the agent made, every tool result, and every response" — and "the SDK writes it to disk automatically so you can return to it later" ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). Returning to a session means the agent comes back with full context: the files it already read, the analysis it already did, the decisions it already made. That's what lets you ask a follow-up after a task finishes, recover after a crash, or branch off to try a different approach without redoing the work.

There are three ways to return, and the exam tests whether you pick the right one: **continue** (resume the most recent session in the directory), **resume** (return to a *specific* session by id), and **fork** (branch a *copy* of a session, leaving the original intact). They look similar and behave very differently. One more thing to keep straight throughout: a session persists the **conversation, not the filesystem** ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)) — resuming restores the transcript, not any files the agent changed.

## How it works

### Capture the id

Resume and fork both need a session id, and you read it off the result. The `session_id` "is present on every result regardless of success or error" — on the `ResultMessage` (in Python it's also nested in `SystemMessage.data`) ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)):

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

session_id = None
async for message in query(
    prompt="Analyze the auth module and suggest improvements",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
):
    if isinstance(message, ResultMessage):
        session_id = message.session_id        # capture it for later
```

### Continue vs. resume

Both pick up an existing session and add to it; they differ in *how they find it* ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)):

- **Continue** (`continue_conversation=True` in Python) finds the **most recent** session in the current directory — no id needed. It's right when your app runs one conversation at a time. `ClaudeSDKClient` does this automatically: each `client.query()` continues the same session within the process.
- **Resume** (`resume=session_id`) returns to a **specific** session you name. It's required "when you have multiple sessions (for example, one per user in a multi-user app) or want to return to one that isn't the most recent" ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).

```python
# Resume a specific past session and build on its context
async for message in query(
    prompt="Now implement the refactoring you suggested",
    options=ClaudeAgentOptions(resume=session_id,
                               allowed_tools=["Read", "Edit", "Write", "Glob", "Grep"]),
):
    ...
```

Common reasons to resume: follow up on a completed task without re-reading files; recover from a run that ended on `error_max_turns` or `error_max_budget_usd` by resuming with a higher limit; or restore a conversation after a process restart ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).

### Fork

Fork is the different one. Using `resume=session_id` together with `fork_session=True` "creates a new session that starts with a copy of the original's history" — "the fork gets its own session ID; the original's ID and history stay unchanged," leaving you "two independent sessions you can resume separately" ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)):

```python
forked_id = None
async for message in query(
    prompt="Instead of JWT, implement OAuth2 for the auth module",
    options=ClaudeAgentOptions(resume=session_id, fork_session=True),
):
    if isinstance(message, ResultMessage):
        forked_id = message.session_id        # the fork's own id, distinct from session_id
```

After this, `session_id` still points at the original JWT thread, unchanged, and `forked_id` is an independent OAuth2 branch. That independence is the whole point: explore an alternative without losing the option to go back. (As with everything here, forking branches the *conversation*, not the filesystem — a forked agent's file edits are real and visible to anything in the same directory ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).)

### The cross-host caveat

Sessions are local files. They live at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`, where `<encoded-cwd>` is "the absolute working directory with every non-alphanumeric character replaced by `-`" — so `/Users/me/proj` becomes `-Users-me-proj` ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). The trap: if a `resume` call runs from a **different** `cwd` (or a different machine), the SDK looks in the wrong place and "returns a fresh session instead of the expected history" — silently. To resume elsewhere, move the `.jsonl` to the same path with a matching `cwd`, or capture the results you need as application state and pass them into a fresh prompt ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).

## Worked example

The three operations together: capture an id, resume it, then fork to branch — modeled as an in-memory `SessionStore` so the semantics are explicit and testable (no disk, no SDK). This is the shape the exercise builds.

```python
import copy


class SessionStore:
    def __init__(self):
        self._sessions = {}
        self._counter = 0

    def _new_id(self):
        self._counter += 1
        return f"sess-{self._counter}"        # deterministic ids, not random

    def create(self, messages=None):
        sid = self._new_id()
        self._sessions[sid] = copy.deepcopy(messages) if messages else []
        return sid

    def append(self, session_id, message):
        if session_id not in self._sessions:
            raise KeyError(session_id)        # never silently create
        self._sessions[session_id].append(message)

    def resume(self, session_id):
        if session_id not in self._sessions:
            raise KeyError(session_id)        # unknown id is an error, not a fresh start
        return self._sessions[session_id]     # the existing transcript, with full context

    def fork(self, session_id):
        if session_id not in self._sessions:
            raise KeyError(session_id)
        fid = self._new_id()
        self._sessions[fid] = copy.deepcopy(self._sessions[session_id])  # a COPY, not an alias
        return fid
```

The two load-bearing lines:

- **`resume` returns the *existing* transcript** and raises on an unknown id. It never quietly starts an empty session — that silent-fresh-session behavior is exactly the cross-host bug above, and modeling resume to *raise* instead makes the failure loud.
- **`fork` deep-copies.** The fork and the original must be independent: appending to one cannot change the other. A shallow copy (or worse, handing back the same list) would alias them, so a "fork" would mutate its parent — the precise opposite of fork's guarantee that "the original's history stays unchanged" ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). `copy.deepcopy` also protects nested message objects, not just the outer list.

## Anti-patterns & pitfalls

1. **Using continue (most-recent) when you need a specific session.** In a multi-user or multi-session app, "the most recent session in this directory" is whatever ran last — likely the wrong user's conversation. When identity of the session matters, capture the `session_id` and `resume` by it; continue is only safe when there's exactly one conversation at a time ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).

2. **Treating fork as in-place continuation — aliasing the original.** Expecting the original to change after a fork, or, in your own state code, sharing the history list so a "fork" mutates its parent. Fork's contract is a *copy*: the original "stays unchanged" and the two are independent ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). If branching one thread silently edits the other, you've built a shallow copy, not a fork.

3. **Re-feeding the whole transcript into a new prompt to "resume."** Pasting the prior conversation into a fresh prompt instead of using `resume=session_id`. It burns context re-establishing what the session already holds and loses fidelity (tool results, internal structure). Resume restores the real session; manual replay approximates it badly.

4. **Resuming across a mismatched `cwd`/host and trusting it worked.** Because a wrong-directory resume returns a *fresh* session silently ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)), an agent that "resumed" can be quietly starting from nothing. Match the `cwd`, move the `.jsonl`, or carry results forward as app state — and don't assume resume succeeded without checking.

5. **Assuming a fork or resume snapshots files.** Sessions persist the conversation, not the filesystem ([Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). To branch and revert file changes you need file checkpointing, a separate mechanism — resuming an old session does not roll back edits the agent made.

## Exam focus

Session management is the Domain 1 answer to "how does this agent remember / branch / recover":

- **Multi-Agent Research System & Customer Support** — per-user or per-investigation sessions resumed by captured id (not "most recent"), and forking to explore alternative directions without losing the main thread.
- **Developer Productivity** — recovering a long Claude Code run after a `max_turns`/budget stop by resuming with a higher limit.

Distractors lean on the confusions above: "use continue" where the session must be specific, a "fork" that mutates the original, manual transcript replay instead of `resume`, or assuming resume works across directories. The correct answer matches the operation to the need — resume by id for a specific session, fork (a true copy) to branch — and respects the cwd rule.

## References & further reading

- [Agent SDK — Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) — capturing `session_id`, the continue/resume/`fork_session` distinction, what fork does and doesn't change, and the `~/.claude/projects/<encoded-cwd>/` cross-host caveat. The single best reference for this lesson.
- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — how turns, messages, and context accumulate *within* a session, which is what resuming restores.

## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.7: Manage session state, resumption, and forking.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
