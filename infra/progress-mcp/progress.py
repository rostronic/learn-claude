"""Core progress-tracking logic for the Learn Claude progress MCP server.

This module is deliberately MCP-free so it can be unit-tested without an MCP
runtime, and runnable as a tiny CLI so commands can record progress via the
Bash tool when the MCP server isn't registered (`python progress.py …`). The
thin MCP wrapper lives in `server.py` and exposes these functions as tools.

What this module does NOT do: call the Anthropic API. It only reads the repo's
curriculum docs (to know which chapters exist) and reads/writes one JSON file.

The progress file is **user data**, so it lives OUTSIDE the repo — at
`~/learn-claude-work/progress.json`, the same home tree where `/verify` and
`/mock-exam` write their results. Nothing here is ever committed.

Locations are resolved at call time so a single env var can redirect them in
tests or alternate checkouts:

- repo root  — `$LEARN_CLAUDE_REPO`, else two levels up from this file
               (`infra/progress-mcp/` → repo root). Used to find `docs/` and `exams/`.
- work dir   — `$LEARN_CLAUDE_WORK_DIR`, else `~/learn-claude-work`. Holds `progress.json`.

Derived data (weak domains, next-step hints, pass counts) is computed on read
in `get_progress()` — it is NEVER stored, so the JSON stays a plain event log.

All public functions raise `ProgressError` on failure. A `ProgressError`
carries a machine-readable `category`, a human `message`, a `retryable` flag,
and an optional actionable `hint`. The MCP wrapper (and the CLI) turn these
into structured error envelopes (`{"error": {...}}`) — mirroring CCA-F Task
Statement 2.2's retryable/non-retryable distinction, which this platform
teaches and therefore dogfoods.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHAPTER_RE = re.compile(r"^\d+\.\d+$")

# A `/verify` score at or above this passes the chapter (matches the /verify
# command's own ">= 80" cutoff). Used only to DERIVE summary fields on read.
PASS_SCORE = 80

# Bounds for a mock-exam scaled score (CCA-F: 100–1000). We accept 0 too, since
# the approximation `round(1000 * fraction)` can floor to 0 on a blank run.
SCALED_MIN = 0
SCALED_MAX = 1000


class ProgressError(Exception):
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
        """Serialize to the `{"error": {...}}` shape the MCP tools return."""
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
    """Repo root holding `docs/` and `exams/`. Override with `$LEARN_CLAUDE_REPO`."""
    env = os.environ.get("LEARN_CLAUDE_REPO")
    if env:
        return Path(env).expanduser().resolve()
    # infra/progress-mcp/progress.py → parents[2] == repo root
    return Path(__file__).resolve().parents[2]


def work_root() -> Path:
    """Root of learner workspaces. Override with `$LEARN_CLAUDE_WORK_DIR`."""
    env = os.environ.get("LEARN_CLAUDE_WORK_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / "learn-claude-work"


def progress_path() -> Path:
    """Path to the single progress JSON (may not exist yet)."""
    return work_root() / "progress.json"


def _now_iso() -> str:
    """UTC timestamp, e.g. `2026-05-29T23:04:11Z` (matches /verify result names)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Curriculum awareness — "what exists" comes from the repo docs, not guesses
# --------------------------------------------------------------------------- #

_MAPPING_CHAPTER_RE = re.compile(r"lesson_chapter:\s*[\"']?(\d+\.\d+)[\"']?")


def _read_text(rel: str) -> str:
    try:
        return (repo_root() / rel).read_text(encoding="utf-8")
    except OSError:
        return ""


def known_chapters() -> tuple[set[str], set[str]]:
    """Return (all_chapters, built_chapters) parsed from the repo docs.

    Reads `docs/curriculum-map.md` (the table of every chapter, with a "built"
    / "planned" status in the last cell) and unions in any `lesson_chapter` ids
    from `docs/exam-mapping.md`. If neither doc is readable, returns empty sets
    — in that case chapter-existence validation is skipped (format is still
    checked). The status is read from the row's last cell specifically, so a
    chapter *titled* "Built-in tools" isn't mistaken for a built one.
    """
    all_chapters: set[str] = set()
    built: set[str] = set()

    for line in _read_text("docs/curriculum-map.md").splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2 or not CHAPTER_RE.match(cells[0]):
            continue
        chapter, status = cells[0], cells[-1]
        all_chapters.add(chapter)
        if "built" in status.lower():
            built.add(chapter)

    for m in _MAPPING_CHAPTER_RE.finditer(_read_text("docs/exam-mapping.md")):
        all_chapters.add(m.group(1))

    return all_chapters, built


def known_exams() -> set[str]:
    """Exam codes that have an `exams/<CODE>/exam.yaml`."""
    exams_dir = repo_root() / "exams"
    if not exams_dir.is_dir():
        return set()
    return {p.name for p in exams_dir.iterdir() if (p / "exam.yaml").exists()}


def _domain_names(exam: str | None) -> dict[str, str]:
    """Best-effort domain-id → name map from `exams/<exam>/exam.yaml`.

    Returns {} if the file or PyYAML is unavailable — names are decoration on
    the weak-domain list, never load-bearing.
    """
    if not exam:
        return {}
    path = repo_root() / "exams" / exam / "exam.yaml"
    if not path.exists():
        return {}
    try:
        import yaml  # local import: names are optional, don't hard-require yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 — any parse failure just drops the names
        return {}
    domains = data.get("domains") or {}
    return {str(k): str(v) for k, v in domains.items()}


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def _validate_chapter(chapter: Any) -> None:
    """Reject malformed ids (invalid_chapter) and unknown ones (unknown_chapter)."""
    if not isinstance(chapter, str) or not CHAPTER_RE.match(chapter):
        raise ProgressError(
            "invalid_chapter",
            f"Chapter must be in module.lesson form (e.g. '3.1'); got {chapter!r}.",
            retryable=False,
            hint="Pass a chapter id like '3.1'.",
        )
    all_chapters, _ = known_chapters()
    if all_chapters and chapter not in all_chapters:
        raise ProgressError(
            "unknown_chapter",
            f"Chapter {chapter} is not in the curriculum (docs/curriculum-map.md).",
            retryable=False,
            hint="Check the chapter id against docs/curriculum-map.md.",
        )


def _validate_score(score: Any) -> int:
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ProgressError(
            "invalid_score",
            f"Score must be a number 0–100; got {score!r}.",
            retryable=False,
        )
    if not (0 <= score <= 100):
        raise ProgressError(
            "invalid_score",
            f"Score must be between 0 and 100; got {score}.",
            retryable=False,
            hint="Pass the verifier's N/100 score.",
        )
    return int(round(score))


def _validate_scaled(scaled: Any) -> int:
    if isinstance(scaled, bool) or not isinstance(scaled, (int, float)):
        raise ProgressError(
            "invalid_scaled",
            f"Scaled score must be a number {SCALED_MIN}–{SCALED_MAX}; got {scaled!r}.",
            retryable=False,
        )
    if not (SCALED_MIN <= scaled <= SCALED_MAX):
        raise ProgressError(
            "invalid_scaled",
            f"Scaled score must be between {SCALED_MIN} and {SCALED_MAX}; got {scaled}.",
            retryable=False,
        )
    return int(round(scaled))


def _validate_per_domain(per_domain: Any) -> dict[str, float]:
    if not isinstance(per_domain, dict) or not per_domain:
        raise ProgressError(
            "invalid_per_domain",
            "per_domain must be a non-empty mapping of domain id → ratio (0–1).",
            retryable=False,
            hint='e.g. {"1": 0.8, "2": 0.5}',
        )
    cleaned: dict[str, float] = {}
    for key, value in per_domain.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0 <= value <= 1):
            raise ProgressError(
                "invalid_per_domain",
                f"per_domain[{key!r}] must be a ratio between 0 and 1; got {value!r}.",
                retryable=False,
            )
        cleaned[str(key)] = float(value)
    return cleaned


def _validate_exam(exam: Any) -> str:
    if not isinstance(exam, str) or not exam.strip():
        raise ProgressError(
            "invalid_exam",
            f"Exam must be a non-empty code (e.g. 'CCAF'); got {exam!r}.",
            retryable=False,
        )
    exams = known_exams()
    if exams and exam not in exams:
        raise ProgressError(
            "unknown_exam",
            f"No exam {exam!r} under exams/. Known: {', '.join(sorted(exams)) or '(none)'}.",
            retryable=False,
            hint="Pass an exam code that has exams/<CODE>/exam.yaml.",
        )
    return exam


# --------------------------------------------------------------------------- #
# State load / save
# --------------------------------------------------------------------------- #


def _empty_state() -> dict[str, Any]:
    return {"chapters": {}, "practice": {}, "mock_exams": [], "updated": None}


def _normalize(data: Any) -> dict[str, Any]:
    """Coerce a loaded blob into the canonical shape, tolerating missing keys."""
    state = _empty_state()
    if isinstance(data, dict):
        if isinstance(data.get("chapters"), dict):
            state["chapters"] = data["chapters"]
        if isinstance(data.get("practice"), dict):
            state["practice"] = data["practice"]
        if isinstance(data.get("mock_exams"), list):
            state["mock_exams"] = data["mock_exams"]
        state["updated"] = data.get("updated")
    return state


def _load_state(*, create: bool) -> dict[str, Any]:
    """Load the progress JSON.

    With `create=False` (reads): a missing work dir is a `work_dir_missing`
    error; a missing file inside an existing work dir is a fresh empty state.
    With `create=True` (writes): the work dir is created on demand and a
    missing file yields an empty state to upsert into.
    """
    root = work_root()
    if not root.exists():
        if not create:
            raise ProgressError(
                "work_dir_missing",
                f"No workspace at {root}.",
                retryable=False,
                hint="Run /study or /exercise <chapter> to start; progress is tracked from there.",
            )
        root.mkdir(parents=True, exist_ok=True)

    path = progress_path()
    if not path.exists():
        return _empty_state()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ProgressError(
            "progress_corrupt",
            f"Could not read progress at {path}: {exc}",
            retryable=False,
            hint="Inspect or delete the file to reset progress tracking.",
        ) from exc

    return _normalize(data)


def _save_state(state: dict[str, Any]) -> None:
    state["updated"] = _now_iso()
    root = work_root()
    root.mkdir(parents=True, exist_ok=True)
    progress_path().write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _ensure_chapter(state: dict[str, Any], chapter: str) -> dict[str, Any]:
    return state["chapters"].setdefault(chapter, {"studied": False, "exercised": False})


# --------------------------------------------------------------------------- #
# Record (upsert) tools
# --------------------------------------------------------------------------- #


def record_study(chapter: str) -> dict[str, Any]:
    """Mark a chapter as studied. Returns {chapter, entry}."""
    _validate_chapter(chapter)
    state = _load_state(create=True)
    entry = _ensure_chapter(state, chapter)
    entry["studied"] = True
    _save_state(state)
    return {"chapter": chapter, "entry": entry}


def record_exercise(chapter: str) -> dict[str, Any]:
    """Mark a chapter's exercise as set up / attempted. Returns {chapter, entry}."""
    _validate_chapter(chapter)
    state = _load_state(create=True)
    entry = _ensure_chapter(state, chapter)
    entry["exercised"] = True
    _save_state(state)
    return {"chapter": chapter, "entry": entry}


def record_verify(chapter: str, score: int) -> dict[str, Any]:
    """Record the verifier's N/100 score for a chapter. Returns {chapter, entry}.

    Stores the latest score, its timestamp, and a derived `passed` flag.
    """
    _validate_chapter(chapter)
    clean = _validate_score(score)
    state = _load_state(create=True)
    entry = _ensure_chapter(state, chapter)
    entry["verified"] = {
        "score": clean,
        "passed": clean >= PASS_SCORE,
        "ts": _now_iso(),
    }
    _save_state(state)
    return {"chapter": chapter, "entry": entry}


def record_practice(chapter: str, correct: bool) -> dict[str, Any]:
    """Append a practice-question attempt for a chapter. Returns {chapter, attempts}."""
    _validate_chapter(chapter)
    if not isinstance(correct, bool):
        raise ProgressError(
            "invalid_input",
            f"`correct` must be a boolean; got {correct!r}.",
            retryable=False,
        )
    state = _load_state(create=True)
    attempts = state["practice"].setdefault(chapter, [])
    attempts.append({"correct": correct, "ts": _now_iso()})
    _save_state(state)
    return {"chapter": chapter, "attempts": attempts}


def record_mock(
    exam: str, scaled: int, passed: bool, per_domain: dict[str, float]
) -> dict[str, Any]:
    """Append a mock-exam result. Returns {entry}.

    `scaled` is the 100–1000 approximation, `passed` is its verdict against the
    exam's threshold, and `per_domain` maps domain id → fraction correct (0–1).
    """
    exam = _validate_exam(exam)
    clean_scaled = _validate_scaled(scaled)
    clean_pd = _validate_per_domain(per_domain)
    if not isinstance(passed, bool):
        raise ProgressError(
            "invalid_input",
            f"`passed` must be a boolean; got {passed!r}.",
            retryable=False,
        )
    state = _load_state(create=True)
    entry = {
        "exam": exam,
        "scaled": clean_scaled,
        "pass": passed,
        "per_domain": clean_pd,
        "ts": _now_iso(),
    }
    state["mock_exams"].append(entry)
    _save_state(state)
    return {"entry": entry}


# --------------------------------------------------------------------------- #
# Read tool + derived summary
# --------------------------------------------------------------------------- #


def _weak_domains(mock: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Domains from the latest mock, lowest ratio first."""
    if not mock:
        return []
    per_domain = mock.get("per_domain") or {}
    names = _domain_names(mock.get("exam"))
    ordered = sorted(per_domain.items(), key=lambda kv: kv[1])
    return [
        {"domain": str(d), "ratio": ratio, "name": names.get(str(d))}
        for d, ratio in ordered
    ]


def _recommend_next(
    built: set[str],
    chapters: dict[str, Any],
    latest_mock: dict[str, Any] | None,
    weak: list[dict[str, Any]],
) -> dict[str, Any]:
    """A single coarse next-step hint. The coach refines this; it just surfaces signal."""
    # 1. A built chapter the learner hasn't studied yet.
    for chapter in sorted(built):
        if not chapters.get(chapter, {}).get("studied"):
            return {
                "action": "study",
                "chapter": chapter,
                "reason": f"Chapter {chapter} is built but not yet studied.",
            }
    # 2. A studied chapter not yet verified-passed.
    for chapter in sorted(built):
        entry = chapters.get(chapter, {})
        if not entry.get("studied"):
            continue
        verified = entry.get("verified")
        if verified and verified.get("score", 0) >= PASS_SCORE:
            continue
        if verified:
            return {
                "action": "verify",
                "chapter": chapter,
                "reason": f"Chapter {chapter} scored {verified['score']} (<{PASS_SCORE}); revise and re-verify.",
            }
        return {
            "action": "exercise",
            "chapter": chapter,
            "reason": f"Chapter {chapter} studied but the exercise isn't verified yet.",
        }
    # 3. Failed the last mock — point at its weakest domain.
    if latest_mock and not latest_mock.get("pass") and weak:
        worst = weak[0]
        label = worst.get("name") or f"domain {worst['domain']}"
        return {
            "action": "review_domain",
            "domain": worst["domain"],
            "reason": f"Lowest mock domain: {label} at {round(worst['ratio'] * 100)}%.",
        }
    # 4. Everything built is passed — take or retake a mock.
    return {
        "action": "mock_exam",
        "reason": "All built chapters are verified; take or retake a mock exam.",
    }


def _summary(state: dict[str, Any]) -> dict[str, Any]:
    all_chapters, built = known_chapters()
    chapters = state["chapters"]
    practice = state["practice"]
    mocks = state["mock_exams"]

    studied = sorted(c for c, e in chapters.items() if e.get("studied"))
    exercised = sorted(c for c, e in chapters.items() if e.get("exercised"))
    verified_passed = sorted(
        c
        for c, e in chapters.items()
        if (e.get("verified") or {}).get("score", 0) >= PASS_SCORE
    )
    verified_attempted = sorted(c for c, e in chapters.items() if e.get("verified"))

    relevant = set(built) | set(chapters) | set(practice)
    per_chapter: dict[str, Any] = {}
    for chapter in sorted(relevant):
        entry = chapters.get(chapter, {})
        attempts = practice.get(chapter, [])
        verified = entry.get("verified") or {}
        per_chapter[chapter] = {
            "built": chapter in built,
            "studied": bool(entry.get("studied")),
            "exercised": bool(entry.get("exercised")),
            "verified_score": verified.get("score"),
            "verified_passed": verified.get("score", 0) >= PASS_SCORE,
            "practice_attempts": len(attempts),
            "practice_correct": sum(1 for a in attempts if a.get("correct")),
        }

    latest_mock = mocks[-1] if mocks else None
    weak = _weak_domains(latest_mock)

    return {
        "pass_score": PASS_SCORE,
        "counts": {
            "chapters_built": len(built),
            "chapters_known": len(all_chapters),
            "studied": len(studied),
            "exercised": len(exercised),
            "verified_attempted": len(verified_attempted),
            "verified_passed": len(verified_passed),
            "mock_exams_taken": len(mocks),
        },
        "built_chapters": sorted(built),
        "studied": studied,
        "verified_passed": verified_passed,
        "per_chapter": per_chapter,
        "latest_mock": latest_mock,
        "weak_domains": weak,
        "recommended_next": _recommend_next(built, chapters, latest_mock, weak),
    }


def get_progress() -> dict[str, Any]:
    """Return the full persisted state plus a derived summary.

    The summary (built vs. studied vs. verified-passed counts, the latest mock,
    weak domains lowest-first, and a coarse next-step hint) is computed here and
    never stored. Raises `work_dir_missing` if no workspace exists yet.
    """
    state = _load_state(create=False)
    return {**state, "summary": _summary(state)}


# --------------------------------------------------------------------------- #
# Tiny CLI — the Bash fallback when the MCP server isn't registered
# --------------------------------------------------------------------------- #


def _parse_bool(raw: str) -> bool:
    lowered = raw.strip().lower()
    if lowered in {"true", "1", "yes", "y", "correct", "pass"}:
        return True
    if lowered in {"false", "0", "no", "n", "incorrect", "fail"}:
        return False
    raise ValueError(f"expected a boolean, got {raw!r}")


_CLI_USAGE = (
    "usage: progress.py <command> [args]\n"
    "  get\n"
    "  study <chapter>\n"
    "  exercise <chapter>\n"
    "  verify <chapter> <score>\n"
    "  practice <chapter> <true|false>\n"
    "  mock <exam> <scaled> <true|false> <per_domain_json>"
)


def _cli(argv: list[str]) -> int:
    if not argv:
        print(_CLI_USAGE, file=sys.stderr)
        return 2
    command, rest = argv[0], argv[1:]
    try:
        if command == "get":
            result = get_progress()
        elif command == "study":
            result = record_study(rest[0])
        elif command == "exercise":
            result = record_exercise(rest[0])
        elif command == "verify":
            result = record_verify(rest[0], int(rest[1]))
        elif command == "practice":
            result = record_practice(rest[0], _parse_bool(rest[1]))
        elif command == "mock":
            result = record_mock(
                rest[0], int(rest[1]), _parse_bool(rest[2]), json.loads(rest[3])
            )
        else:
            raise ProgressError(
                "invalid_command",
                f"Unknown command {command!r}.",
                retryable=False,
                hint=_CLI_USAGE,
            )
    except ProgressError as exc:
        print(json.dumps(exc.to_envelope()))
        return 1
    except (IndexError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"error": {"category": "invalid_args", "message": str(exc), "retryable": False}}
            )
        )
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
