---
chapter: "5.3"
slug: "commands-and-skills"
title: "Custom slash commands and skills"
module: "module-5-claude-code-mcp"
sequence: 18
references:
  - title: "Claude Code — Extend Claude with skills"
    url: "https://code.claude.com/docs/en/skills"
    type: official_docs
    covers: "SKILL.md, frontmatter (name/description/allowed-tools/invocation control), arguments, model vs user invocation"
  - title: "Claude Code — Best practices (Create skills)"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "When to write a skill vs CLAUDE.md; disable-model-invocation for side-effecting workflows"
  - title: "Claude Code — Explore the .claude directory"
    url: "https://code.claude.com/docs/en/claude-directory"
    type: official_docs
    covers: "commands/ and skills/ locations; commands and skills are the same mechanism"
---

# Custom slash commands and skills

## Overview

When you keep pasting the same instructions, checklist, or multi-step procedure
into chat, you've found a skill. A **skill** is a `SKILL.md` file with instructions
that *"Claude adds to its toolkit. Claude uses skills when relevant, or you can
invoke one directly with /skill-name"*
([skills docs](https://code.claude.com/docs/en/skills)).

A note on naming, because the exam (and older docs) use both terms: **custom slash
commands have been merged into skills.** Per the docs, *"A file at
.claude/commands/deploy.md and a skill at .claude/skills/deploy/SKILL.md both
create /deploy and work the same way. Your existing .claude/commands/ files keep
working."* Skills are the recommended form because they add a directory for
supporting files plus invocation control. This lesson (CCAF 3.2) teaches both:
how to author them, how arguments work, and — the part the exam leans on — **who
invokes a skill: you, Claude, or both.**

## How it works

### The file and its frontmatter

A skill is a directory under `.claude/skills/` containing a `SKILL.md`:
*"YAML frontmatter between --- markers that tells Claude when to use the skill, and
markdown content with the instructions Claude follows when the skill runs. The
directory name becomes the command you type, and the description helps Claude decide
when to load the skill automatically."*

```markdown
---
name: summarize-changes
description: Summarizes uncommitted changes and flags anything risky. Use when the user asks what changed, wants a commit message, or asks to review their diff.
---

Summarize the uncommitted changes in this repo and flag anything risky.
```

The frontmatter fields that matter for this task statement:

- **`name`** — display name in listings (defaults to the directory name).
- **`description`** — *"helps Claude decide when to load the skill automatically."*
  This is load-bearing: it's the only part always in context, and it's how Claude
  knows when a skill is relevant. Write it as *what it does + when to use it.*
- **`allowed-tools`** — *"Tools Claude can use without asking permission when this
  skill is active."*
- **`disable-model-invocation`** and **`user-invocable`** — invocation control,
  below.

### Why the body is cheap

The economic point: *"Unlike CLAUDE.md content, a skill's body loads only when it's
used, so long reference material costs almost nothing until you need it."* The
description sits in context; the full instructions load on invocation. That's why
the docs steer procedures and sometimes-relevant domain knowledge *out* of CLAUDE.md
and *into* skills — CLAUDE.md is loaded every session, skills are not.

### Arguments

Skills (and commands) accept arguments you pass after the name. The placeholders:

- **`$ARGUMENTS`** — everything the user typed after the command, as one string.
- **`$1`, `$2`, …** — positional arguments.
- **`$name`** — named arguments declared in the `arguments` frontmatter list.

```markdown
---
name: fix-issue
description: Fix a GitHub issue
disable-model-invocation: true
---
Analyze and fix GitHub issue $ARGUMENTS:
1. Use `gh issue view` to get the details
2. Find the relevant files and implement the fix
3. Write tests, run them, and open a PR
```

Run `/fix-issue 1234` and `$ARGUMENTS` expands to `1234`.

### Who invokes a skill — the key distinction

By default *"both you and Claude can invoke any skill. You can type /skill-name to
invoke it directly, and Claude can load it automatically when relevant."* Two
frontmatter fields restrict that:

| Frontmatter | You can invoke | Claude can invoke | When loaded |
|---|---|---|---|
| (default) | Yes | Yes | Description always in context; body loads when invoked |
| `disable-model-invocation: true` | Yes | **No** | Description **not** in context; body loads when **you** invoke |
| `user-invocable: false` | **No** | Yes | Description always in context; body loads when Claude invokes |

The exam-critical case is **`disable-model-invocation: true`**: *"Use this for
workflows with side effects or that you want to control timing, like /commit,
/deploy, or /send-slack-message. You don't want Claude deciding to deploy because
your code looks ready."* A deploy skill is the canonical example — you author it as
a skill for reuse, but you do **not** want the model triggering a production deploy
on its own judgment. The inverse, `user-invocable: false`, is for background
knowledge Claude should apply when relevant but that isn't a meaningful command for
a human to type (e.g. a `legacy-system-context` skill).

### Where skills live

`.claude/skills/` (project, checked in and shared with the team) or
`~/.claude/skills/` (personal, all your projects), plus plugin-bundled skills.
Same locations idea as CLAUDE.md and rules.

## Worked example: a reusable PR-review command

You review every PR the same way and want one command for it. Because reviewing is
something *you* trigger deliberately (and you don't want Claude auto-running it),
make it user-invoked:

```markdown
---
name: review-pr
description: Review a pull request for correctness, security, and test coverage.
argument-hint: "[pr-number]"
disable-model-invocation: true
allowed-tools: Bash(gh pr view *), Bash(gh pr diff *), Read, Grep
---
Review pull request #$1.

1. Run `gh pr diff $1` to get the change set.
2. Check: correctness bugs, security issues (injection, authz, secrets), and
   whether new code paths have tests.
3. Report findings grouped by severity with file:line references. Do not edit code.
```

Walking through the choices:

- **`disable-model-invocation: true`** — you decide when to review, so Claude
  shouldn't fire it on its own. You still call it with `/review-pr 456`.
- **`$1`** — the PR number, positional. `argument-hint` shows `[pr-number]` in
  autocomplete.
- **`allowed-tools`** — scopes the auto-approved tools to read-only `gh` and file
  inspection, so the command can't be turned into something that *writes*.
- **`description`** — written as what-it-does so listings and (if it were
  model-invokable) auto-loading would be accurate.

Drop this at `.claude/skills/review-pr/SKILL.md`, commit it, and every teammate has
`/review-pr`.

## Anti-patterns & pitfalls

**Letting Claude auto-invoke a side-effecting command.** A `/deploy` or
`/send-slack-message` skill without `disable-model-invocation: true` can be
triggered by the model when it judges the work "done." The docs are explicit: use
`disable-model-invocation: true` for side effects and timing-sensitive workflows.
Forgetting it is the classic mistake this task statement tests.

**A vague `description`.** The description is how Claude decides when to load a
model-invokable skill, and what shows in listings. "Helper for stuff" means the
skill never auto-loads when it should. Write *what it does and when to use it.*

**Putting a procedure in CLAUDE.md instead of a skill.** A multi-step workflow in
CLAUDE.md loads its full text into *every* session, bloating context. *"For domain
knowledge or workflows that are only relevant sometimes, use skills instead. Claude
loads them on demand without bloating every conversation."*

**Over-broad `allowed-tools`.** Granting a command blanket `Bash` when it only needs
`gh pr diff` widens what auto-runs without a prompt. Scope `allowed-tools` to what
the command actually uses.

**Confusing a skill with a subagent.** A skill is reusable *instructions* that run
in your conversation (or are invoked directly); a subagent (Module 3) runs in its
*own* context with its own tools. Reach for a skill to package a workflow; reach for
a subagent to isolate context. They compose, but they aren't the same tool.

## Exam focus

CCAF 3.2 rewards knowing: a skill = `SKILL.md` (frontmatter `name`/`description` +
`allowed-tools`), commands and skills are the same `/name` mechanism, the
`$ARGUMENTS`/`$1` placeholders, and above all the **invocation-control** semantics
— default is both you and Claude; `disable-model-invocation: true` makes it
**user-only** (the right choice for `/deploy` and other side-effecting workflows);
`user-invocable: false` makes it Claude-only. The reliable distractor is a
side-effecting command left model-invokable.

## References & further reading

- [Extend Claude with skills](https://code.claude.com/docs/en/skills) — `SKILL.md`,
  the full frontmatter reference, argument placeholders, and the "control who
  invokes a skill" table.
- [Best practices — Create skills](https://code.claude.com/docs/en/best-practices)
  — when to write a skill vs CLAUDE.md, and `disable-model-invocation` for
  side-effecting workflows.
- [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory)
  — `commands/` and `skills/` locations and that they're the same mechanism.

## Exam coverage

- **CCAF** — Domain 3 (Claude Code & Configuration), Task Statement 3.2: Create and
  configure custom slash commands and skills.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
