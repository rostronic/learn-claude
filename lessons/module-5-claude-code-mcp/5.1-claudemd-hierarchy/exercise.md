# CLAUDE.md hierarchy, scoping & modular organization — exercise

You're given a pure-logic model of Claude Code's memory discovery in
`starter/memory_resolver.py`. No Claude Code process runs and no API is called —
you implement the *load-order rules* the lesson describes (straight from the
official memory docs), and the test suite encodes the contract.

## Setup

```bash
cd ~/learn-claude-work/5.1
pip install -r requirements.txt && pytest
```

Everything is in-memory; there's nothing to install beyond `pytest`.

## Your task

Implement two functions in `starter/memory_resolver.py`:

1. **`resolve_memory(cwd, existing_files, ...)`** — return the CLAUDE.md files that
   load at launch, in **documented load order**:
   - managed policy (if present),
   - then user memory (`~/.claude/CLAUDE.md`) if present,
   - then project memory: the directory tree from the filesystem **root down to
     cwd** (root-most first, cwd last), and within each directory `CLAUDE.md` then
     `CLAUDE.local.md`,
   - including only paths that exist.

   Remember: files **compose** (concatenate), they don't override; and
   `CLAUDE.local.md` is the per-directory *Local instructions* file, not something
   to ignore.

2. **`discover_subtree_memory(cwd, read_file_path, existing_files)`** — model the
   **lazy** discovery of subtree memory: a `CLAUDE.md` *below* `cwd` only activates
   when a file in that subtree is read. Return the subtree CLAUDE.md files on the
   path from `cwd` down to the file being read, nearest-cwd first.

## What we check

See `rubric.yaml`. In short: the project tree is emitted root-down (nearest read
last), managed → user → project load order holds, `CLAUDE.local.md` is appended
after its directory's `CLAUDE.md`, root and subdirectory memory both appear
(compose, not override), and subtree memory is lazy. The full suite must pass.

## When you're done

Run `pytest` until green, then `/verify 5.1`.
