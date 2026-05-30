"""Tests for extract_with_retry. These mock the Anthropic client — no API key needed."""

import copy
from types import SimpleNamespace

import pytest

from extraction_loop import ExtractionFailed, extract_with_retry
from invoice import INVOICE_TOOL, validate_invoice

VALID = {
    "vendor": "Acme",
    "total": 150.0,
    "line_items": [
        {"description": "Widgets", "amount": 100.0},
        {"description": "Gaskets", "amount": 50.0},
    ],
    "due_date": None,
}

# Same vendor/items, but the stated total contradicts the line-item sum (150).
SUM_MISMATCH = {**VALID, "total": 200.0}


def _tool_use_response(tool_input, tool_id="toolu_1", name="record_invoice"):
    """A fake Message with stop_reason tool_use and one tool_use block."""
    block = SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)
    return SimpleNamespace(stop_reason="tool_use", content=[block])


class _Messages:
    def __init__(self, outer):
        self._outer = outer

    def create(self, **kwargs):
        # Snapshot the messages as they were AT CALL TIME (the loop mutates the
        # list in place, so we deep-copy to inspect per-call history later).
        self._outer.calls.append(copy.deepcopy(kwargs.get("messages")))
        self._outer.create_kwargs.append(kwargs)
        return self._outer._responses.pop(0)


class RecordingClient:
    """A fake anthropic.Anthropic() that records each create() call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []           # deep-copied `messages` per call
        self.create_kwargs = []   # full kwargs per call
        self.messages = _Messages(self)

    @property
    def call_count(self):
        return len(self.create_kwargs)


def test_valid_extraction_returns_immediately():
    """A valid first extraction means exactly one API call and no retry."""
    client = RecordingClient([_tool_use_response(VALID)])
    data = extract_with_retry(client, "doc", INVOICE_TOOL, validate_invoice)

    assert client.call_count == 1
    assert data == VALID


def test_retry_feeds_specific_validation_errors_back():
    """On a semantic failure, the retry must include the SPECIFIC errors."""
    client = RecordingClient([
        _tool_use_response(SUM_MISMATCH),  # fails: 100+50 != 200
        _tool_use_response(VALID),         # corrected
    ])
    data = extract_with_retry(client, "doc", INVOICE_TOOL, validate_invoice)

    assert client.call_count == 2
    assert data == VALID

    # The SECOND call's messages must carry a tool_result reporting the error —
    # a bare "try again" (no error text) would not satisfy this.
    second_call_messages = client.calls[1]
    feedback_blocks = [
        b
        for m in second_call_messages
        if isinstance(m.get("content"), list)
        for b in m["content"]
        if isinstance(b, dict) and b.get("type") == "tool_result"
    ]
    assert feedback_blocks, "retry must append a tool_result with feedback"
    joined = " ".join(b.get("content", "") for b in feedback_blocks)
    assert "total" in joined  # the specific discrepancy, not a generic message
    assert any(b.get("is_error") for b in feedback_blocks)


def test_tool_choice_forces_the_named_tool_on_every_attempt():
    """tool_choice must force the extraction tool — including on retries."""
    client = RecordingClient([
        _tool_use_response(SUM_MISMATCH),
        _tool_use_response(VALID),
    ])
    extract_with_retry(client, "doc", INVOICE_TOOL, validate_invoice)

    assert client.call_count == 2
    for kwargs in client.create_kwargs:
        assert kwargs["tool_choice"] == {"type": "tool", "name": INVOICE_TOOL["name"]}


def test_exhausting_attempts_raises_with_unresolved_errors():
    """If the model never satisfies the validator, raise after max_attempts."""
    client = RecordingClient([_tool_use_response(SUM_MISMATCH) for _ in range(3)])
    with pytest.raises(ExtractionFailed) as exc_info:
        extract_with_retry(client, "doc", INVOICE_TOOL, validate_invoice, max_attempts=3)

    assert client.call_count == 3           # capped — did not loop forever
    assert exc_info.value.attempts == 3
    assert exc_info.value.errors            # the unresolved errors are surfaced


def test_validate_invoice_catches_sum_mismatch_but_allows_null_due_date():
    """The semantic validator flags totals that don't add up; null due_date is fine."""
    assert validate_invoice(VALID) == []
    errors = validate_invoice(SUM_MISMATCH)
    assert errors and any("total" in e for e in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
