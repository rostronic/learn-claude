"""Starter skeleton for Learn Claude chapter 2.3 — Structured error responses.

Implement the three functions below. See exercise.md for the full spec.
These are pure logic — no Anthropic API, no API key, no network.

The four exception classes are provided for you; do not change them.
"""


class TransientError(Exception):
    """A temporary failure that may succeed on retry (timeout, 503, rate limit)."""


class ValidationError(Exception):
    """The input was malformed or invalid — retrying the same call fails the same way."""


class BusinessRuleError(Exception):
    """A well-formed request disallowed by business rules (e.g. refund over policy)."""


class PermissionDeniedError(Exception):
    """The caller lacks access to the resource."""


def classify_error(exc: Exception) -> tuple:
    """Return (category, retryable) for an exception.

      TransientError        -> ("transient",  True)
      ValidationError       -> ("validation", False)
      BusinessRuleError     -> ("business",   False)
      PermissionDeniedError -> ("permission", False)
      anything else         -> ("unexpected", False)
    """
    # TODO: implement. Only transient failures are retryable; unknown
    #   exceptions default to ("unexpected", False) — don't blindly retry them.
    raise NotImplementedError("Implement classify_error — see exercise.md")


def to_tool_result(tool_use_id: str, category: str, message: str, retryable: bool) -> dict:
    """Build a structured error tool_result.

    Shape:
      {
        "type": "tool_result",
        "tool_use_id": <tool_use_id>,
        "is_error": True,
        "content": {"error_category": <category>, "retryable": <retryable>, "message": <message>},
      }
    """
    # TODO: implement.
    raise NotImplementedError("Implement to_tool_result — see exercise.md")


def safe_invoke(handler, tool_use_id: str, args: dict) -> dict:
    """Run handler(args) and ALWAYS return a tool_result — never raise.

    Success: {"type": "tool_result", "tool_use_id": <id>, "content": <handler return>}
    Failure: classify the exception and return to_tool_result(...) with the
             exception's message (str(exc), falling back to the category if empty).
    """
    # TODO: implement. Wrap handler(args) in try/except. A bare `except
    #   Exception` is intentional here: an uncaught throw would stop the agent
    #   loop, so convert every failure into a returned is_error result.
    raise NotImplementedError("Implement safe_invoke — see exercise.md")
