---
chapter: "2.1"
slug: "built-in-tools"
title: "Built-in tools (Read, Write, Edit, Bash, Grep, Glob)"
module: "module-2-tools"
sequence: 5
references:
  - title: "Claude Code — Tools reference"
    url: "https://code.claude.com/docs/en/tools-reference"
    type: official_docs
    covers: "The built-in tool table, permission column, and per-tool behavior for Read/Write/Edit/Bash/Grep/Glob"
  - title: "Claude Code — Identity and access (permissions)"
    url: "https://code.claude.com/docs/en/permissions"
    type: official_docs
    covers: "Tool-specific permission rules; Read/Edit path patterns and Bash command patterns"
---

# Built-in tools (Read, Write, Edit, Bash, Grep, Glob)

## Overview

Claude Code ships with a fixed set of **built-in tools** for understanding and modifying a codebase — and Domain 2 expects you to reach for the *right* one rather than shelling everything out through `Bash`. Each tool is a purpose-built capability with its own behavior, output shape, and permission posture: "Claude Code has access to a set of built-in tools that help it understand and modify your codebase" ([Tools reference](https://code.claude.com/docs/en/tools-reference)).

Six of them are the workhorses this lesson covers:

| Tool | What it does | Permission required |
|---|---|---|
| `Read` | Reads file contents (with line numbers) | No |
| `Write` | Creates or overwrites a file with full content | Yes |
| `Edit` | Makes a targeted, exact-string edit to a file | Yes |
| `Bash` | Runs a shell command | Yes |
| `Grep` | Searches *file contents* for a pattern (ripgrep) | No |
| `Glob` | Finds *files by name* pattern | No |

The permission column is not incidental — it's a design signal. The read-only navigation tools (`Read`, `Grep`, `Glob`) require no permission, while the three that touch your machine (`Write`, `Edit`, `Bash`) do ([Tools reference](https://code.claude.com/docs/en/tools-reference)). Picking the narrow tool that already exists for a job is therefore both more reliable *and* less privileged than routing the same work through `Bash`. That is the whole point of CCAF Task Statement 2.5: select and apply built-in tools effectively.

## How it works

The tool names are exact strings — they're what you write in permission rules, subagent `tools` lists, and hook matchers ([Tools reference](https://code.claude.com/docs/en/tools-reference)). So "select a tool" is a literal act: you name `Read`, not "the read capability." Each of the six has behavior worth knowing precisely, because the exam's distractors are built from getting that behavior subtly wrong.

### Read — structured file access, not `cat`

`Read` "takes a file path and returns the contents with line numbers" and is instructed to use absolute paths ([Tools reference — Read](https://code.claude.com/docs/en/tools-reference#read-tool-behavior)). It does more than dump bytes: large files come back paginated with a `PARTIAL view` notice and `offset`/`limit` to read more; images return as visual content (not raw bytes); PDFs read in page ranges; `.ipynb` notebooks return cells with outputs. It reads files, **not directories** — listing a directory is an `ls` via `Bash`. The line numbers matter downstream: they're what makes `Edit` and code references precise.

### Write — full-file create/overwrite

`Write` "creates a new file or overwrites an existing one with the full content provided. It does not append or merge" ([Tools reference — Write](https://code.claude.com/docs/en/tools-reference#write-tool-behavior)). Crucially, **overwriting an existing file requires that you read it first** in the current conversation; a `Write` to an unread existing file fails. The docs are explicit about scope: "For partial changes to an existing file, Claude uses Edit instead of Write." Reach for `Write` to create a new file or do a genuine full rewrite — not to change three lines.

### Edit — exact-string replacement with a safety gate

`Edit` "performs exact string replacement. It takes an `old_string` and a `new_string` and replaces the first with the second. It does not use regex or fuzzy matching" ([Tools reference — Edit](https://code.claude.com/docs/en/tools-reference#edit-tool-behavior)). Three checks gate every edit, in order:

1. **Read-before-edit** — the file must have been read in the current conversation and unchanged on disk since.
2. **Match** — `old_string` must appear exactly, whitespace and all.
3. **Uniqueness** — it must appear exactly once, or you pass a longer context string, or set `replace_all: true`.

This is why `Edit` is the tool for surgical changes: it refuses to guess. The read-before-edit gate is a correctness feature, not an obstacle.

### Bash — the escape hatch, with real limits

`Bash` "executes shell commands in your environment" ([Tools reference — Bash](https://code.claude.com/docs/en/tools-reference#bash-tool-behavior)) and is the right tool for running tests, builds, `git`, package managers, and anything without a dedicated tool. Know its persistence model: a `cd` carries over to later commands only while it stays inside the project (or an added working directory); **environment variables do not persist** across commands (an `export` in one is gone in the next); commands time out at two minutes by default (up to ten with `timeout`); output is capped at 30,000 characters before being spilled to a file. `Bash` is powerful precisely because it's unconstrained — which is also why it requires permission and why you don't use it for jobs a narrower tool already covers.

### Grep — search contents, built on ripgrep

`Grep` "searches file contents for patterns. Where Glob finds files by name, Grep finds lines inside them" ([Tools reference — Grep](https://code.claude.com/docs/en/tools-reference#grep-tool-behavior)). It's built on [ripgrep](https://github.com/BurntSushi/ripgrep) and uses ripgrep regex syntax (so `interface{}` is the pattern `interface\{\}`), with output modes `files_with_matches` (default), `content`, and `count`, and scoping by `glob` or `type`. One behavior to memorize: **Grep respects `.gitignore`** — gitignored files are skipped unless you pass a path directly.

### Glob — find files by name

`Glob` "finds files based on pattern matching" with standard glob syntax including `**` for recursive matching ([Tools reference — Glob](https://code.claude.com/docs/en/tools-reference#glob-tool-behavior)). Results are sorted by modification time and capped at 100 (with a truncation flag when hit). The contrast with `Grep` is exam-bait: **Glob does *not* respect `.gitignore` by default** — it finds gitignored files alongside tracked ones, the opposite of `Grep`.

### Selecting tools is also scoping access

Because tool names are the unit of configuration, "which tools" is a first-class design choice, not just an in-the-moment decision. A named subagent's `tools` field restricts what it can use — "`tools` only: the subagent gets only the listed tools" ([Tools reference — Agent tool behavior](https://code.claude.com/docs/en/tools-reference#agent-tool-behavior)). Stand up a read-only exploration subagent by listing only the navigation tools:

```python
# A read-only code-exploration subagent. Listing only these three removes every
# other tool from its context — omitting the field would let it inherit all tools.
explorer = {
    "description": "Read-only code exploration",
    "tools": ["Read", "Grep", "Glob"],   # navigation only — no Bash/Write/Edit available
}
```

With only `Read`, `Grep`, and `Glob` in scope, the subagent can navigate the tree but has no `Write`, `Edit`, or `Bash` available to modify it or run a shell — the selection bounds its capability. And because those three need no permission, it also runs without prompts. (Distributing tools across agents is the focus of chapter 3.4; here the point is narrower: choosing the right built-in tools is also choosing the right capability boundary. Note that an `allowedTools` *permission* list only auto-approves calls — it's the `tools` *availability* field that removes a tool from the subagent's reach.)

## Worked example

The reusable skill is a decision: *given a concrete file operation, which built-in tool is correct?* Encoding that mapping makes the reasoning explicit — and it's exactly what you'll implement in the exercise. Here it is as runnable Python:

```python
# Map a described operation to the correct built-in tool.
# The mapping encodes the Tools-reference rules: dedicated tools over Bash,
# Edit (targeted) over Write (full overwrite), Grep for contents, Glob for names.

INTENT_TO_TOOL = {
    "read_file": "Read",                  # not `cat` via Bash
    "find_files_by_name": "Glob",         # not `find`
    "search_file_contents": "Grep",       # not `grep`/`rg` via Bash
    "edit_region_of_existing_file": "Edit",  # targeted change, not Write
    "create_or_overwrite_file": "Write",  # full content; new file or true rewrite
    "run_command": "Bash",                # tests, git, builds — no dedicated tool
}

def select_tool(intent: str) -> str:
    try:
        return INTENT_TO_TOOL[intent]
    except KeyError:
        raise ValueError(f"no built-in tool mapped for intent {intent!r}")

def requires_permission(tool: str) -> bool:
    # Per the Tools reference permission column.
    needs = {"Bash", "Edit", "Write", "WebFetch", "WebSearch", "NotebookEdit"}
    safe = {"Read", "Grep", "Glob", "Agent"}
    if tool in needs:
        return True
    if tool in safe:
        return False
    raise ValueError(f"unknown tool {tool!r}")

assert select_tool("search_file_contents") == "Grep"
assert select_tool("read_file") == "Read"
assert requires_permission("Grep") is False
assert requires_permission("Bash") is True
```

Walking through the choices:

- **Search vs. find.** "Search the contents of files" is `Grep`; "find files whose *names* match" is `Glob`. Routing either through `Bash` (`grep -r`, `find`) throws away ripgrep's speed, the structured output modes, and the `.gitignore` handling — and needlessly escalates to a permissioned tool.
- **Edit vs. Write.** A targeted change to an existing file is `Edit`; `Write` is for new files or a full rewrite. The docs say so directly, and `Write` would force re-sending the whole file and risk clobbering content you didn't mean to touch.
- **Read vs. `cat`.** `Read` gives you line numbers (which `Edit` and references depend on), pagination, and image/PDF/notebook handling. A `Bash` `cat` gives you none of that and only *partially* satisfies the read-before-edit gate.
- **`Bash` for the rest.** Running tests, `git`, a build — there's no dedicated tool, so `Bash` is correct. The rule isn't "avoid `Bash`"; it's "don't use `Bash` for a job a purpose-built tool already does."

## Anti-patterns & pitfalls

CCAF Task Statement 2.5 is about applying the built-in tools *effectively* — the distractors are all cases of using a blunt tool where a precise one exists:

1. **Shelling file operations out through `Bash`.** Using `Bash` `cat` to read, `grep`/`find` to search, or `sed -i` to edit when `Read`/`Grep`/`Glob`/`Edit` exist. It's slower, loses structured output and line numbers, requires permission the read tools don't, and bypasses safety gates — `Bash` file reads only satisfy read-before-edit for a narrow set of commands (`cat`, `head`, `tail`, `sed -n`) with no pipes or redirects. Reach for the dedicated tool first.
2. **`Write` for a partial change.** Overwriting an entire file to alter a few lines. The docs prescribe `Edit` for partial changes; `Write` re-sends the whole file and can clobber what you didn't intend. `Write` is for new files or genuine full rewrites.
3. **Editing a file you haven't read.** `Edit` (and `Write` over an existing file) enforce read-before-edit; attempting a blind edit fails. Read first, every time — the gate exists to keep edits anchored to the file's real contents.
4. **Assuming `Grep` and `Glob` treat `.gitignore` the same.** They don't: `Grep` skips gitignored files; `Glob` includes them by default. Expecting `Glob` to hide build artifacts (or `Grep` to surface them) gives you the wrong file set.

The prescribed approach: **use the purpose-built tool for each operation — `Read`/`Grep`/`Glob` for navigation, `Edit` for surgical changes, `Write` for new files, and `Bash` only for work no dedicated tool covers.** This is not a style preference on the exam; the narrow tool is the correct answer and "just use `Bash`" is the trap.

## Exam focus

This task statement underlies every scenario where Claude Code operates on a real repository:

- **Scenario 2 (Code Generation with Claude Code)** and **Scenario 4 (Developer Productivity with Claude)** — generating and modifying code is a stream of `Read` → `Edit`/`Write` with `Grep`/`Glob` to navigate; the right-tool choice is the reliability story.
- **Scenario 5 (Claude Code for Continuous Integration)** — `Bash` runs the test/build commands, but exploration and edits still go through the dedicated tools.

Expect distractors that reach for `Bash` to read, search, or edit ("run `grep -r` to find usages", "overwrite the file with the corrected version"). The correct answer is the purpose-built tool — `Grep` to search, `Edit` to change, `Read` to inspect — with `Bash` reserved for commands that have no dedicated tool.

## References & further reading

- [Claude Code — Tools reference](https://code.claude.com/docs/en/tools-reference) — the built-in tool table with the permission column, plus the per-tool behavior sections for `Read`, `Write`, `Edit`, `Bash`, `Grep`, and `Glob`. The single best reference for this lesson.
- [Claude Code — Identity and access (permissions)](https://code.claude.com/docs/en/permissions) — tool-specific permission rules: `Read(...)`/`Edit(...)` path patterns (shared by `Read`/`Grep`/`Glob` and `Edit`/`Write`/`NotebookEdit`) and `Bash(...)` command-pattern matching.

## Exam coverage

- **CCAF** — Domain 2 (Tool Design & MCP Integration), Task Statement 2.5: Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
