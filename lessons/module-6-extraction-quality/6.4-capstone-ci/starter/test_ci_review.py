"""Tests for the CI review pipeline. Pure logic + a mocked Anthropic client."""

import copy
from types import SimpleNamespace

import pytest

from ci_review import (
    REVIEW_TOOL,
    claude_ci_command,
    format_pr_feedback,
    review_pull_request,
    route_review_job,
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


# --- claude_ci_command (CCAF 3.6) ------------------------------------------

def test_command_is_non_interactive_and_scoped():
    argv = claude_ci_command("Review this PR for security issues", ["Read", "Grep"])

    assert "-p" in argv                                   # headless, no interactive prompts
    assert "Review this PR for security issues" in argv
    i = argv.index("--allowedTools")
    assert argv[i + 1] == "Read,Grep"                     # pre-authorized, scoped tools


def test_command_does_not_disable_all_permissions():
    argv = claude_ci_command("Review", ["Read"])
    assert not any("dangerously" in tok for tok in argv)  # never skip permission checks wholesale


# --- route_review_job (CCAF 4.5) -------------------------------------------

def test_blocking_pre_merge_check_runs_synchronously():
    assert route_review_job({"name": "pre-merge security check", "blocking": True}) == "sync"


def test_overnight_report_runs_as_batch():
    assert route_review_job({"name": "nightly tech-debt report", "blocking": False}) == "batch"


# --- review_pull_request (CCAF 4.6 + 4.1) ----------------------------------

def test_review_is_multi_pass_and_independent():
    files = {"a.py": "AAA", "b.py": "BBB"}
    responses = [
        _findings_response([{"file": "a.py", "category": "correctness", "severity": "high",
                             "issue": "off-by-one", "confidence": 0.9}]),
        _findings_response([{"file": "b.py", "category": "security", "severity": "high",
                             "issue": "sql injection", "confidence": 0.95}]),
        _findings_response([{"file": "a.py", "category": "correctness", "severity": "medium",
                             "issue": "contract mismatch a->b", "confidence": 0.8}]),
    ]
    client = RecordingClient(responses)
    findings = review_pull_request(client, files, {"security", "correctness"})

    # per-file passes + integration pass == 3, NOT a single combined pass
    assert client.call_count == len(files) + 1
    # every review pass is an independent instance — no generator turns threaded in
    assert all(m["role"] != "assistant" for call in client.calls for m in call)
    assert len(findings) == 3


def test_findings_outside_explicit_criteria_are_dropped():
    files = {"a.py": "AAA"}
    responses = [
        _findings_response([
            {"file": "a.py", "category": "security", "severity": "high",
             "issue": "hardcoded secret", "confidence": 0.95},
            {"file": "a.py", "category": "style", "severity": "low",
             "issue": "line too long", "confidence": 0.4},          # out of scope
        ]),
        _findings_response([]),  # integration pass
    ]
    client = RecordingClient(responses)
    findings = review_pull_request(client, files, report_categories={"security"})

    categories = {f["category"] for f in findings}
    assert categories == {"security"}                     # the 'style' nit was filtered out


# --- format_pr_feedback ----------------------------------------------------

def test_feedback_is_actionable_with_location():
    comments = format_pr_feedback([
        {"file": "auth.py", "line": 42, "category": "security", "severity": "high",
         "issue": "SQL injection in query builder"},
    ])
    assert len(comments) == 1
    assert "auth.py:42" in comments[0]
    assert "SQL injection in query builder" in comments[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
