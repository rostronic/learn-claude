"""Starter skeleton for Learn Claude chapter 4.4 — Session state, resumption,
and forking.

Implement the SessionStore below. It's an in-memory model of the Agent SDK's
session semantics: a session is a transcript (list of messages) persisted under
an id; you can resume a specific session by id, and fork one to branch a copy
whose changes don't touch the original. See exercise.md for the full spec.

This is pure logic — no SDK, no disk, no network.
"""

import copy


class SessionStore:
    """An in-memory store of sessions, each a list of messages keyed by id."""

    def __init__(self):
        # TODO: initialize an empty mapping of session_id -> transcript (list),
        # and a deterministic id counter (do NOT use randomness/uuid — tests
        # depend on stable ids like "sess-1", "sess-2", ...).
        raise NotImplementedError("Implement SessionStore.__init__ — see exercise.md")

    def create(self, messages=None) -> str:
        """Create a new session seeded with a COPY of optional `messages`.

        Returns the new session id (e.g. "sess-1"). Seeding with a copy means a
        later mutation of the caller's list does not bleed into the session.
        """
        # TODO: implement
        raise NotImplementedError("Implement create — see exercise.md")

    def append(self, session_id, message) -> None:
        """Append `message` to the given session's transcript.

        Raise KeyError if the session does not exist.
        """
        # TODO: implement
        raise NotImplementedError("Implement append — see exercise.md")

    def resume(self, session_id) -> list:
        """Return the EXISTING session's full transcript.

        The returned list is the live transcript: appends after a resume
        continue the same session (this is resume, not a fresh start). Raise
        KeyError for an unknown id — never silently create a new session.
        """
        # TODO: implement
        raise NotImplementedError("Implement resume — see exercise.md")

    def fork(self, session_id) -> str:
        """Create a NEW session whose transcript is a DEEP COPY of the source's.

        Returns the new (distinct) session id. The original is unchanged, and the
        two sessions are independent: appending to one must not affect the other.
        Raise KeyError if the source does not exist.
        """
        # TODO: implement — use copy.deepcopy so the fork does not alias the
        # source's transcript (or any nested message objects).
        raise NotImplementedError("Implement fork — see exercise.md")
