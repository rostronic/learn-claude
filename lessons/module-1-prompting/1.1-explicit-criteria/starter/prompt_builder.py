"""Starter skeleton for Learn Claude chapter 1.1 — Prompting with explicit criteria.

Implement build_review_prompt below. See exercise.md for the full spec.
"""


def build_review_prompt(report, skip, severity):
    """Build a code-review prompt from explicit, categorical criteria.

    Args:
        report:   list[str] — categories the reviewer MUST report (non-empty).
        skip:     list[str] — categories the reviewer MUST skip (non-empty).
        severity: dict[str, str] — {level: definition anchored to a concrete example} (non-empty).

    Returns:
        str — the assembled prompt.

    Raises:
        ValueError if report, skip, or severity is empty.
    """
    # TODO: implement
    #   1. Raise ValueError if report, skip, or severity is empty.
    #   2. Compose a prompt that lists every REPORT category, every SKIP category, and
    #      each severity level + definition.
    #   3. Add an explicit instruction to flag only issues that clearly meet a REPORT
    #      category — NOT to filter by confidence or be "conservative".
    raise NotImplementedError("Implement build_review_prompt — see exercise.md")
