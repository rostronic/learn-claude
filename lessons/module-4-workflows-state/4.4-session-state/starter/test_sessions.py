"""Tests for SessionStore — an in-memory model of resume/fork semantics.

Pure logic — no SDK, no disk, no network, no API key.
"""

import pytest

from sessions import SessionStore


def test_create_returns_stable_id_and_seeds_transcript():
    store = SessionStore()
    sid = store.create([{"role": "user", "content": "analyze the auth module"}])
    assert sid == "sess-1"
    assert store.resume(sid) == [{"role": "user", "content": "analyze the auth module"}]


def test_create_seeds_with_a_copy_not_the_callers_list():
    store = SessionStore()
    seed = [{"role": "user", "content": "hi"}]
    sid = store.create(seed)
    seed.append({"role": "user", "content": "leak"})  # mutate caller's list afterward
    assert store.resume(sid) == [{"role": "user", "content": "hi"}]


def test_create_with_no_messages_starts_empty():
    store = SessionStore()
    sid = store.create()
    assert store.resume(sid) == []


def test_append_then_resume_reflects_message():
    store = SessionStore()
    sid = store.create()
    store.append(sid, {"role": "assistant", "content": "done"})
    assert store.resume(sid) == [{"role": "assistant", "content": "done"}]


def test_resume_unknown_id_raises_keyerror():
    store = SessionStore()
    with pytest.raises(KeyError):
        store.resume("nope")


def test_append_unknown_id_raises_keyerror():
    store = SessionStore()
    with pytest.raises(KeyError):
        store.append("nope", {"role": "user", "content": "x"})


def test_fork_returns_a_different_id():
    store = SessionStore()
    sid = store.create([{"role": "user", "content": "jwt path"}])
    fid = store.fork(sid)
    assert fid != sid


def test_fork_starts_equal_to_source():
    store = SessionStore()
    sid = store.create([{"role": "user", "content": "jwt path"}])
    fid = store.fork(sid)
    assert store.resume(fid) == store.resume(sid)


def test_appending_to_fork_does_not_change_original():
    store = SessionStore()
    sid = store.create([{"role": "user", "content": "jwt path"}])
    fid = store.fork(sid)
    store.append(fid, {"role": "user", "content": "try oauth2 instead"})
    # The original is untouched — fork branched a copy, not an alias.
    assert store.resume(sid) == [{"role": "user", "content": "jwt path"}]
    assert len(store.resume(fid)) == 2


def test_appending_to_original_does_not_change_fork():
    store = SessionStore()
    sid = store.create([{"role": "user", "content": "jwt path"}])
    fid = store.fork(sid)
    store.append(sid, {"role": "user", "content": "continue jwt"})
    assert len(store.resume(sid)) == 2
    assert store.resume(fid) == [{"role": "user", "content": "jwt path"}]


def test_fork_deep_copies_nested_message_objects():
    store = SessionStore()
    sid = store.create([{"role": "user", "content": {"text": "nested"}}])
    fid = store.fork(sid)
    # Mutating a nested object in the fork must not reach the original.
    store.resume(fid)[0]["content"]["text"] = "mutated"
    assert store.resume(sid)[0]["content"]["text"] == "nested"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
