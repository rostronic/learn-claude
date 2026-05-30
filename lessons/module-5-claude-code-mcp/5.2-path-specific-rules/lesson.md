---
chapter: "5.2"
slug: "path-specific-rules"
title: "Path-specific rules for conditional conventions"
module: "module-5-claude-code-mcp"
sequence: 17
references:
  - title: "Claude Code — Memory: organize rules with .claude/rules/"
    url: "https://code.claude.com/docs/en/memory"
    type: official_docs
    covers: ".claude/rules/, the paths frontmatter, glob patterns, conditional loading"
  - title: "Claude Code — Explore the .claude directory"
    url: "https://code.claude.com/docs/en/claude-directory"
    type: official_docs
    covers: "Where rules live; rules vs CLAUDE.md vs skills"
  - title: "Claude Code — Hooks"
    url: "https://code.claude.com/docs/en/hooks"
    type: official_docs
    covers: "PreToolUse/PostToolUse, matcher by tool name, exit 2 / permissionDecision"
---

# Path-specific rules for conditional conventions

## Overview

Real repos aren't uniform. The Python service wants type hints and `ruff`; the
frontend wants Prettier and no `console.log`; the `migrations/` directory must
never be hand-edited. A single global CLAUDE.md instruction can't express "this
applies *here* but not *there*" without bloating every session with rules that are
irrelevant most of the time.

Claude Code's answer is **path-specific rules**: topic files under `.claude/rules/`
that can carry a `paths:` frontmatter field so they *"only load into context when
Claude works with matching files"*
([memory docs](https://code.claude.com/docs/en/memory)). That's the native
mechanism CCAF 3.3 is about. This lesson teaches it, then draws the line the exam
cares about: rules are **context** (advisory guidance, conditionally loaded); when
a convention must hold **deterministically**, you escalate to a **hook**. Knowing
which tool fits which kind of rule is the skill being tested.

## How it works

### `.claude/rules/` — modular, topic-scoped instructions

Instead of one giant CLAUDE.md, you put each concern in its own file under
`.claude/rules/`: *"This keeps instructions modular and easier for teams to
maintain."* The docs show the shape directly:

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md
│       ├── testing.md
│       └── security.md
```

*"All .md files are discovered recursively,"* so you can nest `frontend/` or
`backend/` subfolders. A rule file **without** a `paths` field loads
unconditionally: *"Rules without paths frontmatter are loaded at launch with the
same priority as .claude/CLAUDE.md."* That alone is just modular organization —
the conditional power comes from `paths`.

### Scoping a rule to file paths

Add a `paths:` list of globs and the rule becomes conditional:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules
- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

Per the docs: *"These conditional rules only apply when Claude is working with
files matching the specified patterns… Rules without a paths field are loaded
unconditionally and apply to all files. Path-scoped rules trigger when Claude reads
files matching the pattern, not on every tool use."* So the API rule above costs
zero context until Claude touches a `src/api/**/*.ts` file — then it activates.

The glob semantics are documented and testable:

| Pattern | Matches |
|---|---|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` |
| `*.md` | Markdown files in the project root |
| `src/components/*.tsx` | React components in that one directory |

You can list multiple patterns and use brace expansion in one:

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
  - "tests/**/*.test.ts"
---
```

The key distinction to internalize: `*` matches within a single path segment (it
does **not** cross `/`), while `**` matches across directory segments. `*.md`
matches `README.md` but **not** `docs/README.md`; `**/*.md` matches both. This is
the same gitignore-style globbing the exercise asks you to implement.

Rules also have scopes, like CLAUDE.md: project rules in `.claude/rules/` and
personal rules in `~/.claude/rules/`, where *"User-level rules are loaded before
project rules, giving project rules higher priority."* This repo dogfoods the
pattern — its `.claude/rules/` files each carry a `paths:` line (e.g. the rubric
rule scopes to `lessons/**/rubric.yaml`) so authoring guidance loads exactly when
you edit a matching file.

### When context isn't enough: hooks

A path-scoped rule makes the right convention **salient**; it does not **guarantee**
compliance. The memory docs are explicit: rules and CLAUDE.md are *"context, not
enforced configuration. To block an action regardless of what Claude decides, use
a PreToolUse hook instead."*

[Hooks](https://code.claude.com/docs/en/hooks) are *"user-defined shell commands…
that execute automatically at specific points in Claude Code's lifecycle,"* giving
*"deterministic control… ensuring certain actions always happen rather than relying
on the LLM."* For a hard path rule you want **`PreToolUse`**, which runs before a
tool call and *can block it*. You configure it in `settings.json` with a **matcher
on the tool name** and a command:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/guard-migrations.sh" }
        ]
      }
    ]
  }
}
```

Two things the exam tests here. First, **the matcher selects the *tool*** (`Edit`,
`Write`, `Bash`), not the file path. The path check happens *inside* the hook,
which receives the tool call as JSON on stdin — including `tool_input` with the
target path. Second, **how the hook blocks**: it can exit with code `2` (*"a
blocking error"* whose stderr is fed back to Claude), or emit a JSON
`permissionDecision` of `"allow"`, `"deny"`, or `"ask"`. A friendly message with
**exit 0 does not block** — exit 0 means allow.

A `PostToolUse` hook on `Edit|Write` is the other half: run `ruff`/`prettier` on
the just-edited path and feed failures back so Claude self-corrects — a
path-conditional quality gate that runs *after* each edit.

## Worked example: one repo, three conventions

A monorepo needs three conditional conventions. The right mechanism differs by the
*kind* of rule:

1. **"In `src/api/`, validate inputs and use the standard error format."** Advisory,
   judgment-based guidance. → A path-scoped **rule**:
   `.claude/rules/api.md` with `paths: ["src/api/**/*.{ts,tsx}"]`. It loads only
   when Claude edits API code, and shapes how it writes — exactly what context is
   for.

2. **"`migrations/**` is read-only to Claude."** Must hold **absolutely**, and is
   mechanically checkable. → A **`PreToolUse` hook** matched to `Edit|Write`: read
   the path from stdin, and if it matches `migrations/**`, exit 2 ("migrations are
   hand-managed; ask a human") or return `permissionDecision: "deny"`. Now the edit
   never lands, regardless of what the model intends.

3. **"Python files must stay `ruff`-clean."** A gate that runs after the edit. → A
   **`PostToolUse` hook** on `Edit|Write`: if the path ends in `.py`, run `ruff
   check`; non-zero feeds the lint errors back so Claude fixes them.

The split is the whole point. (1) is *context* because it's advisory and
judgment-laden — a rule is perfect and a hook would be the wrong tool (you can't
mechanically "check" a style preference). (2) and (3) are *enforced* because they
must hold deterministically and are mechanically decidable — so they're hooks.
Pick by the kind of rule, not by habit.

## Anti-patterns & pitfalls

**Using a prompt instruction to enforce a hard rule.** "Please never touch
`migrations/`" in CLAUDE.md or a rule is *advisory* — the docs say so outright.
Anything that *must* hold goes in a `PreToolUse` hook (exit 2 / `deny`), not in
prose. This is the programmatic-enforcement-over-prompting principle (Domain 1's
1.4) applied to paths, and it's the single most reliable distractor on this task.

**Putting the path glob in the hook's `matcher` field.** The `matcher` selects the
**tool** (`Edit`, `Write`, `Bash`), not the file. `matcher: "migrations/**"`
matches no tool and the hook never fires. The path check belongs *inside* the hook,
which reads `tool_input` from stdin.

**A hook that prints an error but exits 0.** Exit 0 means *allow*. To block you
must exit 2 (or return a `deny` decision). A friendly message with a success exit
code lets the edit through anyway — a silent enforcement failure.

**Forcing a judgment-based preference into a hook.** Not every convention should be
a gate. "Prefer dependency injection" isn't mechanically decidable, and blocking on
it creates friction and false positives. Advisory, judgment-laden conventions
belong in a path-scoped **rule**; reserve hooks for rules that are both *mandatory*
and *checkable*.

**Over-broad `paths` globs.** A rule scoped to `**/*` when it only governs
`src/api/**/*.ts` loads on the wrong edits and reintroduces the context bloat you
used rules to avoid. Remember `*` doesn't cross `/`: scope as tightly as the rule
actually requires.

**Duplicating a rule in both CLAUDE.md and `.claude/rules/`.** Redundant, and the
two can drift and contradict — and *"if two rules contradict each other, Claude may
pick one arbitrarily."* If it's path-specific, it lives in a path-scoped rule; if
it's truly universal, it stays in CLAUDE.md. Not both.

## Exam focus

CCAF 3.3 is "conditional convention loading." Expect questions that hinge on:
**`.claude/rules/` + a `paths:` glob is the native mechanism** for path-specific
*context*; rules without `paths` load globally; `*` vs `**` glob scope; and the
escalation to a **`PreToolUse` hook** (matcher on the **tool**, path checked
**inside**, **exit 2 / deny** to block) when a convention must hold
deterministically. The distractors are the anti-patterns above — most often
"enforce a hard rule with a CLAUDE.md instruction" and "match the path in the hook
matcher."

## References & further reading

- [Memory — organize rules with .claude/rules/](https://code.claude.com/docs/en/memory)
  — the `.claude/rules/` directory, the `paths:` frontmatter, the glob pattern
  table, conditional vs unconditional loading, and user vs project rule precedence.
- [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory)
  — where rules sit relative to CLAUDE.md and skills, and when to use each.
- [Hooks](https://code.claude.com/docs/en/hooks) — `PreToolUse`/`PostToolUse`,
  matchers by tool name, the stdin JSON (`tool_input`), exit-code-2 blocking, and
  the `permissionDecision` allow/deny/ask outputs.

## Exam coverage

- **CCAF** — Domain 3 (Claude Code & Configuration), Task Statement 3.3: Apply
  path-specific rules for conditional convention loading.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
