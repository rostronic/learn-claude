# Session state, resumption, and forking — exercise

## What you're building

An in-memory `SessionStore` that models the Agent SDK's session semantics:
sessions are transcripts persisted under an id; you can `resume` a specific one
by id, and `fork` one to branch an independent copy. Implementing it cleanly
forces the two facts the exam tests — resume returns the *existing* history, and
fork is a *copy*, not an alias.

## Class to implement

```python
class SessionStore:
    def __init__(self): ...
    def create(self, messages=None) -> str:   # returns a stable id like "sess-1"
    def append(self, session_id, message) -> None
    def resume(self, session_id) -> list      # the existing transcript
    def fork(self, session_id) -> str         # a NEW id; deep copy of the source
```

## Requirements

You must:

1. **Generate deterministic ids** — `"sess-1"`, `"sess-2"`, … from an incrementing counter. No `uuid`/randomness (tests depend on stable ids).
2. **`create` seeds with a copy** of the optional `messages` (a later mutation of the caller's list must not bleed in); with no argument it starts empty.
3. **`append` adds a message** to the session's transcript and **raises `KeyError`** for an unknown id.
4. **`resume` returns the existing session's transcript** (the live list, so appends after resume continue the same session) and **raises `KeyError`** for an unknown id — never silently create a new session.
5. **`fork` returns a new, distinct id** whose transcript is a **deep copy** of the source; the source is unchanged and the two are fully independent (appending to one never affects the other, including nested message objects).
6. **Pass every test in `test_sessions.py`.**

You must NOT:

7. **Alias the source transcript in `fork`.** Returning the same list, or a shallow copy that shares nested objects, so that mutating the fork changes the original — that's the opposite of fork's guarantee. Use a deep copy.
8. **Silently start a fresh/empty transcript on `resume` of an unknown id.** Resume must surface the missing session (raise `KeyError`), not quietly return a new empty session.

Requirements 7 and 8 are graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/4.4
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — no Anthropic client, no `ANTHROPIC_API_KEY`, no API
credits. The real SDK persists sessions to disk and exposes the same semantics
via `resume=session_id` and `fork_session=True` on `query()`
(`pip install claude-agent-sdk`); this store makes those semantics explicit and
testable.

When you're ready (or stuck), run `/verify 4.4` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Agent SDK — Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) — capturing `session_id`, `resume` vs. `continue`, `fork_session` (a copy; original unchanged), and the cwd caveat.
