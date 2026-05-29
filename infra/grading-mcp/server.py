"""Learn Claude grading MCP server (Phase 2 infrastructure).

A stdio MCP server that gives the `verifier` subagent deterministic, scriptable
access to a learner's exercise and its rubric. It reads files and runs the
rubric's shell commands — it never calls the Anthropic API. The LLM judging of
`code_review` / `anti_pattern` criteria stays with the verifier.

Tools:
  - load_rubric(chapter)              → parsed rubric (chapter, criteria)
  - load_work(chapter)                → learner source files (paths + contents)
  - run_bash_check(chapter, command)  → {passed, exit_code, stdout, stderr}
  - grade(chapter)                    → rubric + work + every bash result

Every tool returns either its success payload or a structured error envelope
`{"error": {category, message, retryable, hint?}}` — see grading.GradingError.

Run directly for stdio transport:  python server.py
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import grading

mcp = FastMCP("learn-claude-grading")


@mcp.tool()
def load_rubric(chapter: str) -> dict[str, Any]:
    """Load and validate the rubric for a chapter (e.g. "3.1").

    Returns {chapter, criteria, rubric_path}, where each criterion has
    {id, description, weight, check, command?}. On failure returns an error
    envelope with category "invalid_chapter", "rubric_not_found", or
    "rubric_invalid".
    """
    try:
        return grading.load_rubric(chapter)
    except grading.GradingError as exc:
        return exc.to_envelope()


@mcp.tool()
def load_work(chapter: str) -> dict[str, Any]:
    """Read the learner's source files for a chapter.

    Reads from ~/learn-claude-work/<chapter>/, excluding results/ and build
    caches; binary and oversized files are reported under `skipped` instead of
    returned. Use the contents to judge code_review / anti_pattern criteria.

    Returns {chapter, work_dir, files: [{path, content}], skipped: [...]}.
    On failure returns an error envelope; "work_dir_missing" means the learner
    should run /exercise <chapter> first.
    """
    try:
        return grading.load_work(chapter)
    except grading.GradingError as exc:
        return exc.to_envelope()


@mcp.tool()
def run_bash_check(chapter: str, command: str) -> dict[str, Any]:
    """Run a rubric bash_execution `command` in the learner's work dir.

    Returns {passed, exit_code, stdout, stderr, command, work_dir}. A nonzero
    exit code is a normal result (passed=False), not an error. On failure
    returns an error envelope: "work_dir_missing", "invalid_command",
    "command_timeout" (retryable), or "command_failed".
    """
    try:
        return grading.run_bash_check(chapter, command)
    except grading.GradingError as exc:
        return exc.to_envelope()


@mcp.tool()
def grade(chapter: str) -> dict[str, Any]:
    """Load rubric + work and run every bash_execution criterion in one call.

    code_review / anti_pattern criteria come back with status "needs_review"
    for the verifier to judge from the returned file contents. Returns
    {chapter, rubric, work, results: [...]}. On a whole-run failure (bad
    chapter, missing rubric, missing workspace) returns an error envelope.
    """
    try:
        return grading.grade(chapter)
    except grading.GradingError as exc:
        return exc.to_envelope()


if __name__ == "__main__":
    mcp.run()
