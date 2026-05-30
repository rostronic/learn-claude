"""Reference implementation for Learn Claude chapter 6.3 — review architectures.

Implement the three functions below. All of it runs against a (mocked) Anthropic
client — no real API calls. See exercise.md for the full spec.
"""

import os

import anthropic


def _review_pass(client, instruction, review_tool):
    """One review pass: a FRESH single-turn request that returns its findings.

    Each pass starts from a clean context (only the instruction + code) and is
    forced to call the review tool, so the result is structured.
    """
    messages = [{"role": "user", "content": instruction}]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        tools=[review_tool],
        tool_choice={"type": "tool", "name": review_tool["name"]},
        messages=messages,
    )
    block = next(b for b in response.content if b.type == "tool_use")
    return block.input.get("findings", [])


def independent_review(client, code, review_tool):
    """Review code with a fresh, INDEPENDENT instance.

    The reviewer sees only the code under review — never the generator's
    conversation or reasoning context. That independence is what lets it question
    decisions the original author (with all its reasoning loaded) would not.

    Returns the list of findings.
    """
    # TODO: build a FRESH single-turn request containing only the review
    # instruction + the code (do NOT thread in any generator conversation or
    # reasoning context), force review_tool, and return its findings. You can use
    # the _review_pass helper above.
    raise NotImplementedError("Implement independent_review — see exercise.md")


def multi_pass_review(client, files, review_tool):
    """Review a multi-file change as focused per-file passes plus one integration pass.

    Args:
        files: dict mapping file path -> file contents.
    Returns:
        The combined findings from every pass.

    Per-file passes catch LOCAL issues without attention dilution; the final
    integration pass examines CROSS-FILE data flow that no single-file pass sees.
    """
    # TODO:
    #   1. For EACH file, run one focused per-file pass over just that file's
    #      contents (a local-issues review). Collect the findings.
    #   2. Then run ONE more integration pass over all files together, looking for
    #      cross-file data-flow issues. Collect those findings too.
    #   3. Return the combined findings. (Total passes == len(files) + 1.) Do NOT
    #      collapse this into a single combined pass over all files at once.
    raise NotImplementedError("Implement multi_pass_review — see exercise.md")


def route_by_confidence(findings, threshold=0.8):
    """Split findings into auto-actionable vs human-review by self-reported confidence."""
    # TODO: return {"auto": [...], "human_review": [...]} where a finding goes to
    # "auto" iff its "confidence" >= threshold, else "human_review".
    raise NotImplementedError("Implement route_by_confidence — see exercise.md")


if __name__ == "__main__":
    # Optional: run an independent review against the real API after tests pass.
    from review import REVIEW_TOOL

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY to run against the real API.")

    client = anthropic.Anthropic()
    code = "def add(a, b):\n    return a - b  # bug\n"
    print(independent_review(client, code, REVIEW_TOOL))
