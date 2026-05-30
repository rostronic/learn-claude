---
chapter: "5.1"
slug: "claudemd-hierarchy"
title: "CLAUDE.md hierarchy, scoping & modular organization"
module: "module-5-claude-code-mcp"
sequence: 16
references:
  - title: "Claude Code — How Claude remembers your project (memory)"
    url: "https://code.claude.com/docs/en/memory"
    type: official_docs
    covers: "CLAUDE.md scopes & load order, @path imports, .claude/rules/, subtree discovery"
  - title: "Claude Code — Explore the .claude directory"
    url: "https://code.claude.com/docs/en/claude-directory"
    type: official_docs
    covers: "Where CLAUDE.md, settings, rules, skills, and commands live"
  - title: "Claude Code — Best practices"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "Writing an effective CLAUDE.md; keep it short, scope it, import detail"
---

# CLAUDE.md hierarchy, scoping & modular organization

## Overview

`CLAUDE.md` is how you give Claude Code persistent, project-aware instructions
without retyping them every session. *"You write these files in plain text; Claude
reads them at the start of every session"*
([memory docs](https://code.claude.com/docs/en/memory)). It is not one file —
it's a **layered** system, and the layering is the point: organization-wide policy,
team-shared project conventions, and your personal preferences each live in a
different place and **compose** into the context Claude reads at startup.

This task statement (CCAF 3.1) is about getting that layering right: which
instruction belongs at which scope, how the files load and combine, and how to
keep the whole thing modular instead of letting one root file rot into the thing
nobody reads. One framing to hold onto from the docs: CLAUDE.md is *"context, not
enforced configuration"* — it shapes behavior but does not guarantee it. (When a
rule must hold deterministically, that's a hook's job, covered in
[5.2](../5.2-path-specific-rules/lesson.md).)

## How it works

### The scopes, broadest to most specific

CLAUDE.md files live in several locations, each with a different scope. The
[memory docs](https://code.claude.com/docs/en/memory) list them *"in load order,
from broadest scope to most specific, so a project instruction appears in context
after a user instruction"*:

| Scope | Location | For |
|---|---|---|
| **Managed policy** | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS), `/etc/claude-code/CLAUDE.md` (Linux/WSL), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows) | Org-wide instructions managed by IT/DevOps; *"cannot be excluded by individual settings."* |
| **User** | `~/.claude/CLAUDE.md` | Your personal preferences across **all** projects. |
| **Project** | `./CLAUDE.md` **or** `./.claude/CLAUDE.md` (the same scope — either location, not two tiers) | Team-shared, checked into source control. |
| **Local** | `./CLAUDE.local.md` | Your personal **project-specific** notes; add it to `.gitignore`. |

The mental model: managed policy sets the floor everyone stands on, project memory
encodes what *this repo* needs, and user memory carries *your* habits everywhere.
They don't overwrite each other — *"All discovered files are concatenated into
context rather than overriding each other."*

### How files load — up the tree, root-down

Within a project, Claude Code discovers memory by walking the directory tree:
*"Claude Code reads CLAUDE.md files by walking up the directory tree from your
current working directory, checking each directory along the way for CLAUDE.md and
CLAUDE.local.md files."* So launching from `repo/services/api/` loads
`repo/services/api/CLAUDE.md`, `repo/services/CLAUDE.md`, and `repo/CLAUDE.md` —
every CLAUDE.md on the path from cwd up the tree.

The **order** matters for conflicts: *"content is ordered from the filesystem root
down to your working directory… so instructions closer to where you launched
Claude are read last. Within each directory, CLAUDE.local.md is appended after
CLAUDE.md."* Reading last means the most-specific instruction is freshest in
context — the subdirectory layers *on top of* the root, it doesn't replace it.

This answers the classic exam question — *"you have a root CLAUDE.md and a
`frontend/CLAUDE.md`; which applies when you work in `frontend/`?"* **Both.** The
root provides project-wide context; the subdirectory file layers local context on
top, read last. Neither is ignored.

### Lazy discovery downward

Memory *below* your cwd is handled differently: *"Claude also discovers CLAUDE.md
and CLAUDE.local.md files in subdirectories under your current working directory.
Instead of loading them at launch, they are included when Claude reads files in
those subdirectories."* So a `frontend/CLAUDE.md` costs you no context until Claude
actually touches files under `frontend/` — scoping without a context tax.

### Modular organization with imports

A single CLAUDE.md that tries to hold everything becomes the thing nobody reads —
and the docs are blunt that size hurts: *"target under 200 lines per CLAUDE.md
file. Longer files consume more context and reduce adherence."* Two tools keep it
lean.

**`@path` imports.** *"CLAUDE.md files can import additional files using
@path/to/import syntax."* The bounds are testable:

- Both relative and absolute paths work; *"relative paths resolve relative to the
  file containing the import, not the working directory"*, and `@~/…` reaches your
  home dir.
- *"Imported files can recursively import other files, with a maximum depth of
  four hops."*
- Imports **organize but do not shrink** context: *"imported files still load and
  enter the context window at launch."*

```markdown
# Project conventions
See @docs/architecture.md for the system overview and @docs/testing.md for how we
write and run tests. Personal overrides: @~/.claude/my-project-instructions.md
```

**`.claude/rules/`.** For larger projects you can split instructions into topic
files under `.claude/rules/`, and even scope them to file paths — that's the
subject of [5.2](../5.2-path-specific-rules/lesson.md). This repo dogfoods both:
its root [CLAUDE.md](../../../CLAUDE.md) stays the editorial constitution and
delegates path-specific detail to `.claude/rules/`.

## Worked example: scoping a monorepo

You maintain a monorepo: a Python `api/` service and a TypeScript `web/` app.
Where does each instruction go?

- **"Use 4-space indent and type hints"** — Python-specific. Put it near the Python
  code: an `api/CLAUDE.md` (lazy-loaded when Claude works there), or a
  path-scoped rule (5.2) so it loads *only* when editing `.py` files.
- **"Run `pnpm test` before claiming web work is done"** — web-specific; scope it to
  `web/` the same way.
- **"All PRs target `develop`, never `main`"** — repo-wide. Root `./CLAUDE.md`.
- **"I prefer terse explanations and conventional-commit messages"** — that's *you*,
  on every repo. `~/.claude/CLAUDE.md`.
- **"Never write to `customer-data/`"** — must hold for everyone, org-wide. Managed
  policy memory (and, because it *must* hold, back it with a hook — see 5.2).

The test for each line: *who needs this, and where?* Org → managed policy. Whole
team on this repo → project root. One subtree → a nested file or a path rule. Only
you → user memory. When a line fails that test — it's in the root but only matters
for `api/` — it's in the wrong layer, and it's costing every session context for
nothing.

The official "what to put in CLAUDE.md" heuristic sharpens this further: *"For each
line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it.
Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"*

## Anti-patterns & pitfalls

**One monolithic root CLAUDE.md holding everything.** Python rules, frontend
rules, deploy runbooks, and personal style in a single root file means every
session pays the full token cost and *"important rules get lost in the noise."*
Scope subtree content down (nested files or path rules) and pull detail into
imports. Keep the root lean and broadly true.

**Putting personal preferences in the project CLAUDE.md.** Your "be terse" or
"use my logging style" belongs in `~/.claude/CLAUDE.md`, not the team's committed
`./CLAUDE.md`. Committing personal taste forces it on every teammate and pollutes
the shared file. Project-specific *and* personal? That's exactly what the
gitignored `./CLAUDE.local.md` is for.

**Assuming a subdirectory CLAUDE.md replaces the root.** It composes, it doesn't
override — all files concatenate, root-down. Expecting the local file to "win" and
silence the root leads to surprise when root-level rules still apply.

**Treating CLAUDE.md as enforcement.** It's *"context, not enforced
configuration… Claude reads it and tries to follow it, but there's no guarantee of
strict compliance."* A rule that *must* hold — "never edit `migrations/`", "always
run lint before commit" — belongs in a **hook**, not in prose. This is the
programmatic-enforcement-over-prompting principle (5.2, and Domain 1's 1.4)
showing up early.

**Inflating context with imports and expecting savings.** Imports are for
*organization*; the imported bytes still load at launch. To actually reduce
per-session context, scope instructions with path rules or move procedures into
skills — don't just `@import` a giant file.

## Exam focus

CCAF Domain 3 rewards knowing the **mechanics**: the four scopes and that they
*compose* (managed → user → project → local), that the directory tree loads
root-down so the nearest file is read last (precedence by recency, not override),
that subtree files load lazily, and that `@import` has a **four-hop** limit and
organizes-without-shrinking context. Reliable distractors: "the subdirectory file
overrides the root," "personal prefs go in the committed project file,"
"CLAUDE.md can enforce a hard rule," and off-by-one import-depth numbers.

## References & further reading

- [How Claude remembers your project (memory)](https://code.claude.com/docs/en/memory)
  — the authoritative reference for scopes, load order, `@path` imports (four-hop
  limit), `.claude/rules/`, and lazy subtree discovery.
- [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory)
  — where CLAUDE.md, settings, rules, skills, and commands live and how they relate.
- [Best practices](https://code.claude.com/docs/en/best-practices) — writing an
  effective, lean CLAUDE.md; the "would removing this cause a mistake?" test.

## Exam coverage

- **CCAF** — Domain 3 (Claude Code & Configuration), Task Statement 3.1: Configure
  CLAUDE.md files with appropriate hierarchy, scoping, and modular organization.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
