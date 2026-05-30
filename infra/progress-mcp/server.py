"""Learn Claude progress-tracking MCP server (Phase 4 infrastructure).

A stdio MCP server that persists a learner's progress so the Phase-4 `coach`
can recommend what to do next. It reads the repo's curriculum docs (to know
which chapters exist) and reads/writes a single JSON file at
`~/learn-claude-work/progress.json` — user data, outside the repo. It never
calls the Anthropic API.

Tools:
  - get_progress()                          → full state + a derived summary
  - record_study(chapter)                   → mark a chapter studied
  - record_exercise(chapter)                → mark a chapter's exercise set up
  - record_verify(chapter, score)           → record the verifier's N/100 score
  - record_practice(chapter, correct)       → append a practice attempt
  - record_mock(exam, scaled, passed, ...)  → append a mock-exam result

Every tool returns either its success payload or a structured error envelope
`{"error": {category, message, retryable, hint?}}` — see progress.ProgressError.

Run directly for stdio transport:  python server.py
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import progress

mcp = FastMCP("learn-claude-progress")


@mcp.tool()
def get_progress() -> dict[str, Any]:
    """Return the learner's full persisted progress plus a derived summary.

    The summary reports chapters built vs. studied vs. verified-passed, the
    latest mock exam, the weakest domains (lowest per-domain ratio first), and a
    coarse next-step hint — all computed on read, never stored. On failure
    returns an error envelope; "work_dir_missing" means the learner hasn't
    studied anything yet (run /study or /exercise to begin tracking).
    """
    try:
        return progress.get_progress()
    except progress.ProgressError as exc:
        return exc.to_envelope()


@mcp.tool()
def record_study(chapter: str) -> dict[str, Any]:
    """Mark a chapter (e.g. "3.1") as studied. Returns {chapter, entry}.

    On failure returns an error envelope: "invalid_chapter" (bad form) or
    "unknown_chapter" (not in docs/curriculum-map.md).
    """
    try:
        return progress.record_study(chapter)
    except progress.ProgressError as exc:
        return exc.to_envelope()


@mcp.tool()
def record_exercise(chapter: str) -> dict[str, Any]:
    """Mark a chapter's exercise as set up / attempted. Returns {chapter, entry}."""
    try:
        return progress.record_exercise(chapter)
    except progress.ProgressError as exc:
        return exc.to_envelope()


@mcp.tool()
def record_verify(chapter: str, score: int) -> dict[str, Any]:
    """Record the verifier's N/100 score for a chapter. Returns {chapter, entry}.

    Stores the latest score plus a derived `passed` flag (>= 80). On failure
    returns an error envelope: "invalid_chapter", "unknown_chapter", or
    "invalid_score" (outside 0–100).
    """
    try:
        return progress.record_verify(chapter, score)
    except progress.ProgressError as exc:
        return exc.to_envelope()


@mcp.tool()
def record_practice(chapter: str, correct: bool) -> dict[str, Any]:
    """Append a practice-question attempt for a chapter. Returns {chapter, attempts}.

    On failure returns an error envelope: "invalid_chapter", "unknown_chapter",
    or "invalid_input" (non-boolean `correct`).
    """
    try:
        return progress.record_practice(chapter, correct)
    except progress.ProgressError as exc:
        return exc.to_envelope()


@mcp.tool()
def record_mock(
    exam: str, scaled: int, passed: bool, per_domain: dict[str, float]
) -> dict[str, Any]:
    """Append a mock-exam result. Returns {entry}.

    `scaled` is the 100–1000 approximation, `passed` its verdict, and
    `per_domain` maps domain id → fraction correct (0–1). On failure returns an
    error envelope: "invalid_exam"/"unknown_exam", "invalid_scaled",
    "invalid_per_domain", or "invalid_input".
    """
    try:
        return progress.record_mock(exam, scaled, passed, per_domain)
    except progress.ProgressError as exc:
        return exc.to_envelope()


if __name__ == "__main__":
    mcp.run()
