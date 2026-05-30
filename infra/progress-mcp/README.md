# Learn Claude — progress-tracking MCP server

Phase 4 **infrastructure** (not coursework). A small [MCP](https://modelcontextprotocol.io)
server that **persists a learner's progress** so the Phase-4 `coach` can turn a
history into "here's exactly what to do next."

It lives here — `infra/progress-mcp/` — and **never** under `lessons/`. A
lesson's `starter/` contains only what a learner runs; servers are platform
plumbing. See the "Infrastructure vs. coursework" rule in
[`.claude/CLAUDE.md`](../../.claude/CLAUDE.md).

## What it does (and doesn't)

It **reads the repo's curriculum docs** (to know which chapters exist and which
are built) and **reads/writes one JSON file** of progress events. That's it.

It does **not** call the Anthropic API. It holds no answer keys and makes no
judgments — the `verifier` produces the scores and the `examiner` grades the
questions; this server just records what they returned and derives a few
summary signals on read.

## Where the data lives (outside the repo)

The progress file is **user data**, so — like `/verify`'s `results/` and
`/mock-exam`'s saved runs — it lives in the learner's home tree, **never in the
repo**:

```
~/learn-claude-work/progress.json
```

Override the location with `$LEARN_CLAUDE_WORK_DIR` (the same var the grading
server and the commands already use). `record_*` creates the file (and the work
dir) on first write; `get_progress` reports `work_dir_missing` until the learner
has studied or exercised at least once.

## Schema

A single JSON object. **Only recorded events are stored** — derived data (weak
domains, pass counts, next-step hints) is computed on read, never persisted.

```json
{
  "chapters": {
    "3.1": { "studied": true, "exercised": true,
             "verified": { "score": 92, "passed": true, "ts": "2026-05-29T23:04:11Z" } }
  },
  "practice": {
    "3.1": [ { "correct": true, "ts": "2026-05-29T23:01:00Z" } ]
  },
  "mock_exams": [
    { "exam": "CCAF", "scaled": 760, "pass": true,
      "per_domain": { "1": 0.8, "2": 0.6, "5": 0.4 }, "ts": "2026-05-29T22:50:00Z" }
  ],
  "updated": "2026-05-29T23:04:11Z"
}
```

A chapter "passes" verification at **score ≥ 80** (matching `/verify`). That's a
derived flag — `get_progress` recomputes it; the stored `passed` is a convenience
mirror.

## Tools

| Tool | Returns |
|---|---|
| `get_progress()` | The full state **plus a derived `summary`** — counts (built vs. studied vs. verified-passed), `built_chapters`, `per_chapter` rollups, the `latest_mock`, `weak_domains` (lowest per-domain ratio first, named from `exam.yaml`), and a coarse `recommended_next` hint. |
| `record_study(chapter)` | `{chapter, entry}` — marks the chapter studied. |
| `record_exercise(chapter)` | `{chapter, entry}` — marks the chapter's exercise set up. |
| `record_verify(chapter, score)` | `{chapter, entry}` — records the verifier's `N/100` score + derived `passed`. |
| `record_practice(chapter, correct)` | `{chapter, attempts}` — appends a practice attempt. |
| `record_mock(exam, scaled, passed, per_domain)` | `{entry}` — appends a mock-exam result. |

`chapter` is the course id in `module.lesson` form (e.g. `"3.1"`); `exam` is an
exam code (e.g. `"CCAF"`). The `coach` subagent reads `get_progress`; the
`/study`, `/verify`, `/practice`, and `/mock-exam` commands call the matching
`record_*` (with a Bash fallback — see below).

## Structured errors

Every tool returns either its success payload or an error envelope — never a
raw stack trace:

```json
{ "error": { "category": "unknown_chapter", "message": "...", "retryable": false, "hint": "..." } }
```

This mirrors **CCA-F Task Statement 2.2** (retryable vs. non-retryable error
handling) — the platform teaches it, so the platform dogfoods it.

| `category` | `retryable` | Meaning / caller action |
|---|---|---|
| `invalid_chapter` | false | Not `module.lesson` form. Pass e.g. `"3.1"`. |
| `unknown_chapter` | false | Well-formed but absent from `docs/curriculum-map.md`. |
| `invalid_score` | false | `record_verify` score outside 0–100. |
| `invalid_scaled` | false | `record_mock` scaled score outside 0–1000. |
| `invalid_per_domain` | false | `record_mock` per-domain map empty or a ratio outside 0–1. |
| `invalid_exam` / `unknown_exam` | false | Blank exam code, or one with no `exams/<CODE>/exam.yaml`. |
| `invalid_input` | false | Non-boolean `correct` / `passed`. |
| `work_dir_missing` | false | No `~/learn-claude-work/` yet (read before any record). |
| `progress_corrupt` | false | `progress.json` won't parse. Inspect or delete to reset. |

## Requirements & layout

- **Python 3.10+** (the `mcp` SDK requires it).
- `pip install -r requirements.txt` → `mcp`, `PyYAML`, `pytest`.

```
infra/progress-mcp/
  server.py          # FastMCP wrapper — exposes the six tools over stdio
  progress.py        # all logic (MCP-free, unit-tested) + a tiny CLI (Bash fallback)
  test_progress.py   # pytest suite (temp fake repo + isolated work dir)
  requirements.txt
  README.md
```

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `LEARN_CLAUDE_REPO` | two levels up from `server.py` (the repo root) | Where `docs/` and `exams/` live. |
| `LEARN_CLAUDE_WORK_DIR` | `~/learn-claude-work` | Holds `progress.json`. |

The repo-root default works out of the box from this checkout; the env vars
exist mainly for tests and alternate layouts.

## Registering the server

**The repo already ships a project [`.mcp.json`](../../.mcp.json) at the root**
that registers this server as `learn-claude-progress`
(`python3 infra/progress-mcp/server.py`), alongside `learn-claude-grading`. So
the only setup a learner needs is installing the requirements
(`pip install -r infra/progress-mcp/requirements.txt`) into the `python3`
Claude Code will use; when they open the repo, Claude Code prompts to start the
server.

To register it manually from a Python 3.10+ environment that has the
requirements installed:

```bash
claude mcp add learn-claude-progress -- python /absolute/path/to/infra/progress-mcp/server.py
```

Or add it to `.mcp.json` / your MCP client config:

```json
{
  "mcpServers": {
    "learn-claude-progress": {
      "command": "python",
      "args": ["/absolute/path/to/infra/progress-mcp/server.py"]
    }
  }
}
```

If you use a virtualenv, point `command` at that interpreter (e.g.
`infra/progress-mcp/.venv/bin/python`) so `mcp` and `PyYAML` resolve.

## The Bash fallback (`progress.py` as a CLI)

Progress tracking must never block a lesson, so the commands record
**optionally**: they call the MCP tool when it's registered, and otherwise fall
back to the same logic via a tiny CLI — reusing the exact validation and file
format, so the recorded data is identical either way:

```bash
python3 infra/progress-mcp/progress.py study 3.1
python3 infra/progress-mcp/progress.py exercise 3.1
python3 infra/progress-mcp/progress.py verify 3.1 92
python3 infra/progress-mcp/progress.py practice 3.1 true
python3 infra/progress-mcp/progress.py mock CCAF 760 true '{"1":0.8,"5":0.4}'
python3 infra/progress-mcp/progress.py get
```

Each prints its JSON result (or an error envelope) and exits non-zero on error.

## Tests

```bash
cd infra/progress-mcp
pip install -r requirements.txt
pytest
```

The suite wires a temp fake repo (a minimal curriculum map, exam mapping, and
one `exam.yaml`) and an isolated work dir through the env vars above, so it
never touches the real repo, the real `~/learn-claude-work`, the network, or
the Anthropic API.
