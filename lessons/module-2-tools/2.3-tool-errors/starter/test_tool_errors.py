"""Tests for the structured-error tool wrapper. Pure logic — no API key needed."""

import pytest

from tool_errors import (
    BusinessRuleError,
    PermissionDeniedError,
    TransientError,
    ValidationError,
    classify_error,
    safe_invoke,
    to_tool_result,
)


@pytest.mark.parametrize(
    "exc,category,retryable",
    [
        (TransientError("503"), "transient", True),
        (ValidationError("bad input"), "validation", False),
        (BusinessRuleError("over policy"), "business", False),
        (PermissionDeniedError("no access"), "permission", False),
        (RuntimeError("???"), "unexpected", False),
        (KeyError("k"), "unexpected", False),
    ],
)
def test_classify_error(exc, category, retryable):
    assert classify_error(exc) == (category, retryable)


def test_only_transient_is_retryable():
    assert classify_error(TransientError("x"))[1] is True
    for exc in (ValidationError("x"), BusinessRuleError("x"), PermissionDeniedError("x")):
        assert classify_error(exc)[1] is False


def test_to_tool_result_shape():
    result = to_tool_result("toolu_1", "transient", "Retry after 60 seconds.", True)
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "toolu_1"
    assert result["is_error"] is True
    assert result["content"]["error_category"] == "transient"
    assert result["content"]["retryable"] is True
    assert result["content"]["message"] == "Retry after 60 seconds."


def test_safe_invoke_success_has_no_error_flag():
    def handler(args):
        return {"value": args["x"] * 2}

    result = safe_invoke(handler, "toolu_ok", {"x": 21})
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "toolu_ok"
    assert result["content"] == {"value": 42}
    assert result.get("is_error") is not True  # success must not be flagged as error


def test_safe_invoke_catches_transient_and_marks_retryable():
    def handler(args):
        raise TransientError("weather service unavailable (HTTP 503)")

    result = safe_invoke(handler, "toolu_t", {})
    assert result["is_error"] is True
    assert result["content"]["error_category"] == "transient"
    assert result["content"]["retryable"] is True
    assert "503" in result["content"]["message"]


def test_safe_invoke_catches_validation_not_retryable():
    def handler(args):
        raise ValidationError("missing required 'location'")

    result = safe_invoke(handler, "toolu_v", {})
    assert result["is_error"] is True
    assert result["content"]["error_category"] == "validation"
    assert result["content"]["retryable"] is False


def test_safe_invoke_never_propagates_unknown_exception():
    """The central rule: a throw would stop the loop, so safe_invoke must catch it."""
    def handler(args):
        raise RuntimeError("kaboom")

    # Must NOT raise — must return a structured error result.
    result = safe_invoke(handler, "toolu_u", {})
    assert result["is_error"] is True
    assert result["content"]["error_category"] == "unexpected"
    assert result["content"]["retryable"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
