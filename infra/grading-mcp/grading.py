"""Core grading logic for the Learn Claude grading MCP server.

This module is deliberately MCP-free so it can be unit-tested without an MCP
runtime. The thin MCP wrapper lives in `server.py` and simply exposes these
functions as tools.

What this module does NOT do: call the Anthropic API. It only reads files and
runs shell commands. The LLM judging of `code_review` / `anti_pattern`
criteria is the verifier subagent's job, not the server's.

Locations are resolved at call time so a single env var can redirect them in
tests or alternate checkouts:

- repo root        — `$LEARN_CLAUDE_REPO`, else two levels up from this file
                     (`infra/grading-mcp/` → repo root).
- learner work dir — `$LEARN_CLAUDE_WORK_DIR`, else `~/learn-claude-work`.
- bash timeout     — `$LEARN_CLAUDE_GRADING_TIMEOUT` seconds, else 120.

All public functions raise `GradingError` on failure. A `GradingError` carries
a machine-readable `category`, a human `message`, a `retryable` flag, and an
optional actionable `hint`. The MCP wrapper turns these into structured error
envelopes (`{"error": {...}}`) — mirroring CCA-F Task Statement 2.2's
distinction between retryable and non-retryable failures, which this platform
teaches and therefore dogfoods.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

CHAPTER_RE = re.compile(r"^\d+\.\d+$")

# Directories never surfaced as "learner work": the verifier's own output and
# build/test caches. `results/` is where /verify writes its graded reports.
EXCLUDED_DIR_NAMES = {
    "results",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
}

# Per-file cap so load_work never returns a multi-megabyte blob to the verifier.
DEFAULT_MAX_FILE_BYTES = 256 * 1024
# Cap on captured stdout/stderr per bash check.
MAX_OUTPUT_CHARS = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 120


class GradingError(Exception):
    """A structured, categorized failure.

    Attributes:
        category:  machine-readable error class (e.g. "work_dir_missing").
        retryable: whether retrying the same call could plausibly succeed.
        hint:      optional actionable next step for the caller / learner.
    """

    def __init__(
        self,
        category: str,
        message: str,
        *,
        retryable: bool = False,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.message = message
        self.retryable = retryable
        self.hint = hint

    def to_envelope(self) -> dict[str, Any]:
        """Serialize to the `{"error": {...}}` shape MCP tools return."""
        error: dict[str, Any] = {
            "category": self.category,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.hint:
            error["hint"] = self.hint
        return {"error": error}


# --------------------------------------------------------------------------- #
# Location resolution
# --------------------------------------------------------------------------- #


def repo_root() -> Path:
    """Repo root holding `lessons/`. Override with `$LEARN_CLAUDE_REPO`."""
    env = os.environ.get("LEARN_CLAUDE_REPO")
    if env:
        return Path(env).expanduser().resolve()
    # infra/grading-mcp/grading.py → parents[2] == repo root
    return Path(__file__).resolve().parents[2]


def work_root() -> Path:
    """Root of learner workspaces. Override with `$LEARN_CLAUDE_WORK_DIR`."""
    env = os.environ.get("LEARN_CLAUDE_WORK_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / "learn-claude-work"


def _timeout_seconds() -> int:
    raw = os.environ.get("LEARN_CLAUDE_GRADING_TIMEOUT")
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_TIMEOUT_SECONDS


def _validate_chapter(chapter: Any) -> None:
    if not isinstance(chapter, str) or not CHAPTER_RE.match(chapter):
        raise GradingError(
            "invalid_chapter",
            f"Chapter must be in module.lesson form (e.g. '3.1'); got {chapter!r}.",
            retryable=False,
            hint="Pass a chapter id like '3.1'.",
        )


def find_lesson_dir(chapter: str) -> Path:
    """Locate `lessons/*/<chapter>-*/` for a chapter id.

    Raises GradingError("rubric_not_found") if no lesson directory matches.
    """
    _validate_chapter(chapter)
    root = repo_root()
    # The dash in the glob keeps "3.1" from matching "3.10-...".
    matches = sorted(p for p in root.glob(f"lessons/*/{chapter}-*") if p.is_dir())
    if not matches:
        raise GradingError(
            "rubric_not_found",
            f"No lesson directory found for chapter {chapter} under {root / 'lessons'}.",
            retryable=False,
            hint=f"Check the chapter id, or confirm $LEARN_CLAUDE_REPO points at the repo (currently {root}).",
        )
    return matches[0]


def work_dir_for(chapter: str) -> Path:
    """Path to the learner's workspace for a chapter (may not exist)."""
    _validate_chapter(chapter)
    return work_root() / chapter


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #


def load_rubric(chapter: str) -> dict[str, Any]:
    """Parse and lightly validate the chapter's rubric.yaml.

    Returns {chapter, criteria, rubric_path}. Raises GradingError with
    category "rubric_not_found" or "rubric_invalid".
    """
    lesson_dir = find_lesson_dir(chapter)
    rubric_path = lesson_dir / "rubric.yaml"
    if not rubric_path.exists():
        raise GradingError(
            "rubric_not_found",
            f"No rubric.yaml in {lesson_dir}.",
            retryable=False,
        )

    try:
        data = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        raise GradingError(
            "rubric_invalid",
            f"Could not parse {rubric_path}: {exc}",
            retryable=False,
        ) from exc

    if not isinstance(data, dict) or not isinstance(data.get("criteria"), list):
        raise GradingError(
            "rubric_invalid",
            f"{rubric_path} must be a mapping with a top-level `criteria` list.",
            retryable=False,
        )

    criteria: list[dict[str, Any]] = []
    for index, raw in enumerate(data["criteria"]):
        if not isinstance(raw, dict):
            raise GradingError(
                "rubric_invalid",
                f"criteria[{index}] in {rubric_path} is not a mapping.",
                retryable=False,
            )
        missing = [k for k in ("id", "description", "weight", "check") if k not in raw]
        if missing:
            raise GradingError(
                "rubric_invalid",
                f"criteria[{index}] in {rubric_path} is missing keys: {', '.join(missing)}.",
                retryable=False,
            )
        if raw["check"] == "bash_execution" and not raw.get("command"):
            raise GradingError(
                "rubric_invalid",
                f"criteria[{index}] ({raw['id']}) is bash_execution but has no `command`.",
                retryable=False,
            )
        criteria.append(raw)

    rel_path = rubric_path
    try:
        rel_path = rubric_path.relative_to(repo_root())
    except ValueError:
        pass

    return {
        "chapter": data.get("chapter", chapter),
        "criteria": criteria,
        "rubric_path": str(rel_path),
    }


def load_work(chapter: str, max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> dict[str, Any]:
    """Read the learner's source files under the work dir.

    Returns {chapter, work_dir, files: [{path, content}], skipped: [...]}.
    Excludes `results/` and build/test caches. Skips binary and oversized
    files (reporting them in `skipped` rather than failing).

    Raises GradingError("work_dir_missing") if the workspace does not exist.
    """
    work_dir = work_dir_for(chapter)
    if not work_dir.is_dir():
        raise GradingError(
            "work_dir_missing",
            f"No workspace at {work_dir}.",
            retryable=False,
            hint=f"Run /exercise {chapter} to set up your workspace, then edit the files there.",
        )

    files: list[dict[str, str]] = []
    skipped: list[dict[str, Any]] = []

    for path in sorted(work_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(work_dir)
        if any(part in EXCLUDED_DIR_NAMES or part.endswith(".egg-info") for part in rel.parts):
            continue

        try:
            raw = path.read_bytes()
        except OSError as exc:
            skipped.append({"path": str(rel), "reason": "unreadable", "detail": str(exc)})
            continue

        if len(raw) > max_file_bytes:
            skipped.append({"path": str(rel), "reason": "too_large", "bytes": len(raw)})
            continue

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append({"path": str(rel), "reason": "binary", "bytes": len(raw)})
            continue

        files.append({"path": str(rel), "content": content})

    return {
        "chapter": chapter,
        "work_dir": str(work_dir),
        "files": files,
        "skipped": skipped,
    }


def _truncate(text: str) -> str:
    if text is None:
        return ""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n…[truncated; {len(text)} chars total]"


def run_bash_check(chapter: str, command: str, timeout: int | None = None) -> dict[str, Any]:
    """Run a rubric `command` inside the learner's work dir.

    Returns {passed, exit_code, stdout, stderr, command, work_dir}. A nonzero
    exit code is a *result* (passed=False), not an error.

    Raises GradingError for situations that aren't a clean pass/fail:
      - "work_dir_missing": no workspace to run in (non-retryable).
      - "invalid_command":  empty/non-string command (non-retryable).
      - "command_timeout":  command exceeded the timeout (retryable).
      - "command_failed":   command could not be launched at all (non-retryable).
    """
    work_dir = work_dir_for(chapter)
    if not work_dir.is_dir():
        raise GradingError(
            "work_dir_missing",
            f"No workspace at {work_dir}.",
            retryable=False,
            hint=f"Run /exercise {chapter} to set up your workspace first.",
        )
    if not isinstance(command, str) or not command.strip():
        raise GradingError(
            "invalid_command",
            "A non-empty shell command is required.",
            retryable=False,
        )

    effective_timeout = timeout if (timeout and timeout > 0) else _timeout_seconds()

    try:
        proc = subprocess.run(  # noqa: S602 — running a trusted rubric command by design
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise GradingError(
            "command_timeout",
            f"Command exceeded {effective_timeout}s: {command}",
            retryable=True,
            hint="The check may be slow or hung; retry, or raise $LEARN_CLAUDE_GRADING_TIMEOUT.",
        ) from exc
    except OSError as exc:
        raise GradingError(
            "command_failed",
            f"Could not launch command {command!r}: {exc}",
            retryable=False,
        ) from exc

    return {
        "passed": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": _truncate(proc.stdout),
        "stderr": _truncate(proc.stderr),
        "command": command,
        "work_dir": str(work_dir),
    }


def grade(chapter: str) -> dict[str, Any]:
    """One-call convenience for the verifier.

    Returns the rubric, the learner's work, and the result of running every
    `bash_execution` criterion. `code_review` / `anti_pattern` criteria are
    returned with status "needs_review" — those are the verifier's LLM call,
    not this server's. A bash criterion that errors (e.g. timeout) is recorded
    as status "error" with its envelope, so one bad check never sinks the rest.

    Raises GradingError only for whole-run failures (bad chapter, missing
    rubric, missing workspace).
    """
    rubric = load_rubric(chapter)
    work = load_work(chapter)

    results: list[dict[str, Any]] = []
    for criterion in rubric["criteria"]:
        entry: dict[str, Any] = {
            "id": criterion["id"],
            "check": criterion["check"],
            "weight": criterion.get("weight"),
        }
        if criterion["check"] == "bash_execution":
            try:
                run = run_bash_check(chapter, criterion["command"])
                entry["status"] = "pass" if run["passed"] else "fail"
                entry["result"] = run
            except GradingError as exc:
                entry["status"] = "error"
                entry.update(exc.to_envelope())
        else:
            entry["status"] = "needs_review"
            entry["description"] = criterion["description"]
        results.append(entry)

    return {
        "chapter": chapter,
        "rubric": rubric,
        "work": work,
        "results": results,
    }
