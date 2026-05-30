"""Reference implementation for Learn Claude chapter 6.1 — validation-retry loop.

Implement extract_with_retry below. See exercise.md for the full spec.
"""

import os

import anthropic


class ExtractionFailed(Exception):
    """Raised when the validator still reports errors after max_attempts.

    `errors` holds the unresolved validation errors so the caller can decide
    whether to escalate to a human (e.g. when a value is simply absent from the
    source) rather than retry further.
    """

    def __init__(self, errors, attempts):
        self.errors = errors
        self.attempts = attempts
        super().__init__(f"unresolved after {attempts} attempt(s): {errors}")


def extract_with_retry(client, document, tool, validate, max_attempts=3):
    """Extract structured data, retrying with specific error feedback on failure.

    Args:
        client:       an anthropic.Anthropic() instance.
        document:     str — the source text to extract from.
        tool:         dict — the Claude tool-use schema to force (e.g. INVOICE_TOOL).
        validate:     callable(data: dict) -> list[str] — returns validation error
                      strings; an empty list means the extraction is valid.
        max_attempts: int — hard cap on attempts (a backstop, not the stop signal).

    Returns:
        The validated extraction dict (the first one for which validate() is empty).

    Raises:
        ExtractionFailed: if validate() still reports errors after max_attempts.
    """
    # TODO: implement the validation-retry loop.
    #   1. Build the initial `messages` with the document, asking the model to
    #      call `tool` to extract.
    #   2. Loop up to max_attempts times. Each pass:
    #        a. client.messages.create(..., tools=[tool],
    #           tool_choice={"type": "tool", "name": tool["name"]}, messages=messages)
    #           — force the tool EVERY attempt so a correction can't escape as prose.
    #        b. Read the extraction off the tool_use block's `input`.
    #        c. errors = validate(data). If empty -> return data (the real exit).
    #        d. Otherwise append the assistant turn, then a user turn whose
    #           tool_result reports the SPECIFIC errors (with is_error: True), and
    #           loop. A bare "try again" without the errors is the anti-pattern.
    #   3. If the loop exhausts without a clean validation, raise
    #      ExtractionFailed(errors, max_attempts). Do NOT loop forever.
    raise NotImplementedError("Implement extract_with_retry — see exercise.md")


if __name__ == "__main__":
    # Optional: try the loop against the real API after the tests pass.
    # Requires ANTHROPIC_API_KEY in the environment.
    from invoice import INVOICE_TOOL, SAMPLE_INVOICE, validate_invoice

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY to run against the real API.")

    client = anthropic.Anthropic()
    result = extract_with_retry(client, SAMPLE_INVOICE, INVOICE_TOOL, validate_invoice)
    print(result)
