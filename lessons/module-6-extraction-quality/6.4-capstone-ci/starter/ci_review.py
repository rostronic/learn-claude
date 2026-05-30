"""Reference implementation for Learn Claude chapter 6.4 — capstone: Claude Code for CI.

A small CI code-review pipeline that ties the module together:
  - build a non-interactive Claude Code invocation        (CCAF 3.6)
  - route review jobs to sync vs batch                     (CCAF 4.5)
  - review a PR with independent, multi-pass review        (CCAF 4.6)
  - filter findings to explicit categories to cut noise    (CCAF 4.1)

Everything runs against pure data or a (mocked) Anthropic client — no real API
calls. See exercise.md for the full spec.
"""

# The structured-findings tool each review pass is forced to call. Each finding
# carries a category (so we can filter to the team's explicit criteria), a
# confidence (for routing), and a detected_pattern (for false-positive analysis).
REVIEW_TOOL = {
    "name": "report_findings",
    "description": "Report code-review findings on a pull request as structured data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "category": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "issue": {"type": "string"},
                        "confidence": {"type": "number"},
                        "detected_pattern": {"type": "string"},
                    },
                    "required": ["file", "category", "severity", "issue"],
                },
            },
        },
        "required": ["findings"],
    },
}


def claude_ci_command(prompt, allowed_tools, output_format="json"):
    """Build the argv for a non-interactive Claude Code review in CI.

    CI has no human to answer permission prompts, so the run must be headless
    (-p / --print) with its tool scope pre-authorized (--allowedTools) — and it
    must NOT disable permission checks wholesale.

    Returns:
        A list of argv tokens.
    """
    # TODO: build argv that runs Claude Code NON-INTERACTIVELY in CI:
    #   - the "-p" (print) flag so it never waits on an interactive prompt
    #   - the prompt
    #   - "--allowedTools" with the comma-joined allowed_tools (scope exactly what
    #     the job needs — do NOT disable permission checks wholesale)
    #   - "--output-format" with output_format so CI can parse the result
    raise NotImplementedError("Implement claude_ci_command — see exercise.md")


def route_review_job(job):
    """Route a review job to "sync" or "batch".

    A blocking pre-merge check needs a synchronous answer; a latency-tolerant job
    (overnight tech-debt report) goes to the batch API for 50% savings.
    """
    # TODO: return "sync" for blocking jobs, "batch" otherwise.
    raise NotImplementedError("Implement route_review_job — see exercise.md")


def _review_pass(client, instruction, review_tool):
    """One independent review pass: a FRESH single-turn request returning findings."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        tools=[review_tool],
        tool_choice={"type": "tool", "name": review_tool["name"]},
        messages=[{"role": "user", "content": instruction}],
    )
    block = next(b for b in response.content if b.type == "tool_use")
    return block.input.get("findings", [])


def review_pull_request(client, files, report_categories, review_tool=REVIEW_TOOL):
    """Review a PR with independent, multi-pass review, filtered to explicit criteria.

    - Independent + multi-pass (4.6): a focused pass per file plus one integration
      pass, each a fresh instance (no generation context carried in).
    - Explicit criteria (4.1): keep only findings whose category is in
      report_categories; dropping out-of-scope categories (e.g. stylistic nits) is
      how you minimize false positives and keep developers trusting the bot.

    Returns:
        The filtered list of findings.
    """
    # TODO:
    #   1. Run a focused independent pass over EACH file (use _review_pass), then
    #      one integration pass over all files together. Collect all findings.
    #      (len(files) + 1 passes; each pass is a fresh, independent instance.)
    #   2. Filter: keep only findings whose "category" is in report_categories.
    #      Dropping out-of-scope categories is how you minimize false positives.
    raise NotImplementedError("Implement review_pull_request — see exercise.md")


def format_pr_feedback(findings):
    """Render findings as actionable PR comment lines."""
    # TODO: return a list of strings like "<file>:<line> [<severity>] <issue>"
    # (omit ":<line>" when a finding has no line).
    raise NotImplementedError("Implement format_pr_feedback — see exercise.md")
