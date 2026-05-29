"""Tests for build_review_prompt. Pure logic — no API key, no model calls."""

import pytest

from prompt_builder import build_review_prompt

REPORT = ["Bugs: code that produces incorrect behavior",
          "Security: injection, auth bypass, secret leakage"]
SKIP = ["Minor style (formatting, naming)", "Local conventions you can't verify"]
SEVERITY = {
    "critical": "data loss or security breach (e.g. unsanitized SQL string interpolation)",
    "minor": "low-blast-radius correctness issue (e.g. off-by-one in a log line)",
}


def test_raises_on_empty_inputs():
    with pytest.raises(ValueError):
        build_review_prompt([], SKIP, SEVERITY)
    with pytest.raises(ValueError):
        build_review_prompt(REPORT, [], SEVERITY)
    with pytest.raises(ValueError):
        build_review_prompt(REPORT, SKIP, {})


def test_includes_every_report_and_skip_category():
    prompt = build_review_prompt(REPORT, SKIP, SEVERITY)
    for c in REPORT + SKIP:
        assert c in prompt


def test_includes_each_severity_level_and_definition():
    prompt = build_review_prompt(REPORT, SKIP, SEVERITY)
    for level, definition in SEVERITY.items():
        assert level in prompt
        assert definition in prompt


def test_instructs_criteria_not_confidence():
    """The prompt must steer on criteria, not on a confidence dial."""
    prompt = build_review_prompt(REPORT, SKIP, SEVERITY).lower()
    # It should reference flagging by the listed categories/criteria...
    assert "categor" in prompt or "criteria" in prompt
    # ...and explicitly tell the model not to filter by confidence.
    assert "confidence" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
