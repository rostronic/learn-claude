"""Tests for the review architecture toolkit. Mocked Anthropic client — no API key."""

import copy
from types import SimpleNamespace

import pytest

from review import REVIEW_TOOL
from review_architecture import (
    independent_review,
    multi_pass_review,
    route_by_confidence,
)


def _findings_response(findings):
    block = SimpleNamespace(type="tool_use", id="toolu_1", name="report_findings",
                            input={"findings": findings})
    return SimpleNamespace(stop_reason="tool_use", content=[block])


class _Messages:
    def __init__(self, outer):
        self._outer = outer

    def create(self, **kwargs):
        self._outer.calls.append(copy.deepcopy(kwargs.get("messages")))
        self._outer.create_kwargs.append(kwargs)
        return self._outer._responses.pop(0)


class RecordingClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.create_kwargs = []
        self.messages = _Messages(self)

    @property
    def call_count(self):
        return len(self.create_kwargs)


# --- independent_review ----------------------------------------------------

def test_independent_review_starts_from_a_clean_context():
    """The reviewer must see ONLY the code — no generator turns (no assistant
    history threaded in). Independence is the whole point of 4.6."""
    client = RecordingClient([_findings_response([{"file": "x.py", "issue": "bug",
                                                   "severity": "high", "confidence": 0.9}])])
    code = "def add(a, b): return a - b"
    findings = independent_review(client, code, REVIEW_TOOL)

    assert client.call_count == 1
    sent_messages = client.calls[0]
    # A fresh instance: no assistant/reasoning turns carried over from generation.
    assert all(m["role"] != "assistant" for m in sent_messages)
    # ...and the code under review is present.
    assert any(code in str(m.get("content", "")) for m in sent_messages)
    assert findings[0]["issue"] == "bug"


def test_independent_review_forces_the_review_tool():
    client = RecordingClient([_findings_response([])])
    independent_review(client, "code", REVIEW_TOOL)
    assert client.create_kwargs[0]["tool_choice"] == {"type": "tool", "name": "report_findings"}


# --- multi_pass_review -----------------------------------------------------

def test_multi_pass_runs_one_pass_per_file_plus_one_integration_pass():
    files = {"a.py": "AAA", "b.py": "BBB", "c.py": "CCC"}
    responses = [
        _findings_response([{"file": "a.py", "issue": "i1", "severity": "low", "confidence": 0.5}]),
        _findings_response([{"file": "b.py", "issue": "i2", "severity": "low", "confidence": 0.5}]),
        _findings_response([{"file": "c.py", "issue": "i3", "severity": "low", "confidence": 0.5}]),
        _findings_response([{"file": "a.py->b.py", "issue": "i4", "severity": "high", "confidence": 0.9}]),
    ]
    client = RecordingClient(responses)
    findings = multi_pass_review(client, files, REVIEW_TOOL)

    # 3 per-file passes + 1 integration pass — NOT a single combined pass.
    assert client.call_count == len(files) + 1
    assert len(findings) == 4


def test_per_file_passes_isolate_one_file_and_integration_sees_all():
    files = {"a.py": "AAA", "b.py": "BBB"}
    client = RecordingClient([_findings_response([]) for _ in range(3)])
    multi_pass_review(client, files, REVIEW_TOOL)

    first_pass = str(client.calls[0])
    second_pass = str(client.calls[1])
    integration_pass = str(client.calls[2])

    # Each per-file pass focuses on a single file's content.
    assert "AAA" in first_pass and "BBB" not in first_pass
    assert "BBB" in second_pass and "AAA" not in second_pass
    # The integration pass sees all files together (cross-file data flow).
    assert "AAA" in integration_pass and "BBB" in integration_pass


# --- route_by_confidence ---------------------------------------------------

def test_route_by_confidence_splits_on_threshold():
    findings = [
        {"file": "a", "issue": "high-conf", "severity": "high", "confidence": 0.95},
        {"file": "b", "issue": "low-conf", "severity": "low", "confidence": 0.40},
        {"file": "c", "issue": "borderline", "severity": "medium", "confidence": 0.80},
    ]
    routed = route_by_confidence(findings, threshold=0.8)

    assert [f["issue"] for f in routed["auto"]] == ["high-conf", "borderline"]
    assert [f["issue"] for f in routed["human_review"]] == ["low-conf"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
