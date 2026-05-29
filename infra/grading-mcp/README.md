# Learn Claude — grading MCP server

Phase 2 **infrastructure** (not coursework). A small [MCP](https://modelcontextprotocol.io)
server that gives the `verifier` subagent deterministic, scriptable access to a
learner's exercise and its rubric, so grading is reproducible instead of done
by eyeball.

It lives here — `infra/grading-mcp/` — and **never** under `lessons/`. A
lesson's `starter/` contains only what a learner runs; graders and servers are
platform plumbing. See the "Infrastructure vs. coursework" rule in
[`.claude/CLAUDE.md`](../../.claude/CLAUDE.md).

## What it does (and doesn't)

It **reads files and runs the rubric's shell commands**. That's it.

It does **not** call the Anthropic API. Judging the `code_review` and
`anti_pattern` criteria — the part that needs a model — stays with the
verifier subagent. This server hands the verifier the raw material (rubric +
work + bash results); the verifier does the reasoning. Keeping the LLM out of
the server is what makes its output deterministic and cheap to test.

## How grading is wired

- **Rubrics** live with each lesson: `lessons/<module>/<chapter>-<slug>/rubric.yaml`.
  Schema (see [`.claude/rules/rubric-authoring.md`](../../.claude/rules/rubric-authoring.md)):
  top-level `chapter` plus a `criteria` list of
  `{id, description, weight, check: code_review|anti_pattern|bash_execution, command?}`.
- **Learner work** lives **outside** the repo at `~/learn-claude-work/<chapter>/`,
  copied from the lesson's `starter/` by `/exercise`. Grading reads from there;
  the verifier writes its reports to `<chapter>/results/`, which this server
  excludes from `load_work`.

## Tools

| Tool | Returns |
|---|---|
| `load_rubric(chapter)` | `{chapter, criteria, rubric_path}` — the parsed, validated rubric. |
| `load_work(chapter)` | `{chapter, work_dir, files: [{path, content}], skipped: [...]}` — the learner's source, excluding `results/` and build caches. Binary/oversized files land in `skipped`. |
| `run_bash_check(chapter, command)` | `{passed, exit_code, stdout, stderr, command, work_dir}` — runs `command` inside the work dir. A nonzero exit is `passed: false`, not an error. |
| `grade(chapter)` | `{chapter, rubric, work, results: [...]}` — runs every `bash_execution` criterion and returns the rest as `needs_review` for the verifier to judge. |

`chapter` is the course id in `module.lesson` form (e.g. `"3.1"`).

## Structured errors

Every tool returns either its success payload or an error envelope — never a
raw stack trace:

```json
{ "error": { "category": "work_dir_missing", "message": "...", "retryable": false, "hint": "Run /exercise 3.1 ..." } }
```

This mirrors **CCA-F Task Statement 2.2** (retryable vs. non-retryable error
handling) — the platform teaches it, so the platform dogfoods it.

| `category` | `retryable` | Meaning / caller action |
|---|---|---|
| `invalid_chapter` | false | Not `module.lesson` form. Pass e.g. `"3.1"`. |
| `rubric_not_found` | false | No lesson dir or `rubric.yaml` for that chapter. |
| `rubric_invalid` | false | `rubric.yaml` won't parse or fails schema (missing keys, bash criterion with no `command`). |
| `work_dir_missing` | false | No `~/learn-claude-work/<chapter>/`. Tell the learner to run `/exercise <chapter>`. |
| `invalid_command` | false | Empty/blank command passed to `run_bash_check`. |
| `command_timeout` | **true** | Command exceeded the timeout. Retry, or raise `LEARN_CLAUDE_GRADING_TIMEOUT`. |
| `command_failed` | false | Command could not be launched at all (e.g. no shell). |

`grade()` records a per-criterion bash error inline (`status: "error"` with the
envelope) so one bad check never sinks the whole report; it only raises for
whole-run failures (bad chapter, missing rubric, missing workspace).

## Requirements & layout

- **Python 3.10+** (the `mcp` SDK requires it).
- `pip install -r requirements.txt` → `mcp`, `PyYAML`, `pytest`.

```
infra/grading-mcp/
  server.py          # FastMCP wrapper — exposes the four tools over stdio
  grading.py         # all logic (MCP-free, unit-tested)
  test_grading.py    # pytest suite (temp fake repo + mocked subprocess)
  requirements.txt
  README.md
```

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `LEARN_CLAUDE_REPO` | two levels up from `server.py` (the repo root) | Where `lessons/` lives. |
| `LEARN_CLAUDE_WORK_DIR` | `~/learn-claude-work` | Root of learner workspaces. |
| `LEARN_CLAUDE_GRADING_TIMEOUT` | `120` | Per-`run_bash_check` timeout, seconds. |

The repo-root default works out of the box from this checkout; the env vars
exist mainly for tests and alternate layouts.

## Registering the server

**The repo already ships a project [`.mcp.json`](../../.mcp.json) at the root** that
registers this server as `learn-claude-grading` (`python3 infra/grading-mcp/server.py`).
So the only setup a learner needs is installing the requirements
(`pip install -r infra/grading-mcp/requirements.txt`) into the `python3` Claude Code
will use; when they open the repo, Claude Code prompts to start the server, and it's
running by the time they reach `/verify`. The options below are for manual or alternate
setups (e.g. pointing at a virtualenv interpreter).

The server speaks MCP over **stdio**. To register it manually from a Python 3.10+
environment that has the requirements installed:

```bash
claude mcp add learn-claude-grading -- python /absolute/path/to/infra/grading-mcp/server.py
```

Or add it to `.mcp.json` / your MCP client config:

```json
{
  "mcpServers": {
    "learn-claude-grading": {
      "command": "python",
      "args": ["/absolute/path/to/infra/grading-mcp/server.py"]
    }
  }
}
```

If you use a virtualenv, point `command` at that interpreter (e.g.
`infra/grading-mcp/.venv/bin/python`) so `mcp` and `PyYAML` resolve.

When these tools are registered, `/verify` routes `bash_execution` criteria
through `run_bash_check`; when they aren't, it falls back to the Bash tool. The
grade is identical either way.

## Tests

```bash
cd infra/grading-mcp
pip install -r requirements.txt
pytest
```

The suite wires a temp fake repo and workspace through the env vars above and
monkeypatches `subprocess.run`, so it never touches the real repo, the real
`~/learn-claude-work`, the network, or the Anthropic API.
