"""Tests for manage_context. The fake summarizer makes runs deterministic;
no Anthropic API key or network is required.
"""

from context_manager import manage_context
from fixtures import fake_summarizer, sample_conversation


def _total(messages):
    return sum(m["tokens"] for m in messages)


def test_system_message_always_preserved():
    convo = sample_conversation()
    result = manage_context(convo, token_budget=100, summarizer=fake_summarizer, keep_recent=4)
    systems = [m for m in result if m["role"] == "system"]
    assert systems, "the pinned system message must survive"
    # The original standing instruction (with the account ID) is still present
    # verbatim as the first message.
    assert result[0]["role"] == "system"
    assert result[0]["content"] == convo[0]["content"]


def test_recent_turns_preserved_verbatim():
    convo = sample_conversation()
    keep = 4
    result = manage_context(convo, token_budget=100, summarizer=fake_summarizer, keep_recent=keep)
    # The last `keep` messages of the result must be exactly the last `keep`
    # non-system messages of the input, unchanged.
    expected_tail = convo[-keep:]
    assert result[-keep:] == expected_tail


def test_over_budget_triggers_summarization():
    convo = sample_conversation()
    assert _total(convo) > 100  # fixture is over this budget
    result = manage_context(convo, token_budget=100, summarizer=fake_summarizer, keep_recent=4)

    # The conversation got shorter (the middle was collapsed).
    assert len(result) < len(convo)

    # Exactly one summary message produced by the fake summarizer.
    summaries = [m for m in result if str(m["content"]).startswith("SUMMARY:")]
    assert len(summaries) == 1

    # The summary sits immediately after the pinned system prompt (head),
    # NOT at the end (which would bury the recent turns / lose-in-the-middle).
    assert result[0]["role"] == "system"
    assert result[0]["content"] == convo[0]["content"]
    assert str(result[1]["content"]).startswith("SUMMARY:")


def test_under_budget_returned_unchanged():
    convo = sample_conversation()
    big = _total(convo) + 1000
    result = manage_context(convo, token_budget=big, summarizer=fake_summarizer, keep_recent=4)
    # Nothing to do: same messages, same order, no summary inserted.
    assert result == convo
    assert not any(str(m["content"]).startswith("SUMMARY:") for m in result)


def test_result_within_budget():
    convo = sample_conversation()
    budget = 200
    result = manage_context(convo, token_budget=budget, summarizer=fake_summarizer, keep_recent=4)
    assert _total(result) <= budget


def test_every_message_keeps_a_tokens_int():
    convo = sample_conversation()
    result = manage_context(convo, token_budget=100, summarizer=fake_summarizer, keep_recent=4)
    for m in result:
        assert isinstance(m["tokens"], int)
