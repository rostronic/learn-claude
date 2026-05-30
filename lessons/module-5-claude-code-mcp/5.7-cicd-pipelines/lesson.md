---
chapter: "5.7"
slug: "cicd-pipelines"
title: "Claude Code in CI/CD pipelines"
module: "module-5-claude-code-mcp"
sequence: 22
references:
  - title: "Claude Code — GitHub Actions"
    url: "https://code.claude.com/docs/en/github-actions"
    type: official_docs
    covers: "claude-code-action, @claude triggers, claude_args, API-key secrets, Bedrock/Vertex"
  - title: "Claude Code — Run Claude Code programmatically (headless)"
    url: "https://code.claude.com/docs/en/headless"
    type: official_docs
    covers: "claude -p, --output-format, --allowedTools, --permission-mode, --bare, fan-out"
  - title: "Claude Code — Best practices (non-interactive mode, fan-out)"
    url: "https://code.claude.com/docs/en/best-practices"
    type: official_docs
    covers: "claude -p in CI, scoping permissions, parallel invocations"
---

# Claude Code in CI/CD pipelines

## Overview

Everything so far assumed one human at a terminal. CCAF 3.6 is about the other mode:
Claude Code running **non-interactively** inside automation — CI pipelines, pre-commit
hooks, scheduled jobs, batch migrations. Two surfaces matter: the **GitHub Action**
(`anthropics/claude-code-action`) for repo-event automation, and **headless mode**
(`claude -p`) for any script or pipeline.

The mechanics are straightforward; the part the exam treats as load-bearing is doing
it **safely and deterministically** — secrets via CI secret storage (never committed),
permissions scoped down because no human is there to approve, and output formats you
can parse. This lesson covers both surfaces and the guardrails.

## How it works

### Headless mode: `claude -p`

*"With `claude -p 'your prompt'`, you can run Claude non-interactively, without a
session"* ([headless docs](https://code.claude.com/docs/en/headless)). It reads stdin
and writes stdout like any Unix tool, so it drops into pipelines:

```bash
git log --oneline -20 | claude -p "summarize these recent commits"
```

The flags that make it CI-ready:

- **`--output-format`** — `text` (default), `json` (*"structured JSON with result,
  session ID, and metadata"*), or `stream-json` for real-time events. Use `json` and
  parse with `jq` when a script consumes the result.
- **`--allowedTools`** — *"let Claude use certain tools without prompting,"* e.g.
  `--allowedTools "Bash,Read,Edit"`. In automation there's no one to approve prompts,
  so you pre-authorize exactly what's needed.
- **`--permission-mode`** — set a baseline. `dontAsk` *"denies anything not in your
  permissions.allow rules… useful for locked-down CI runs"*; `acceptEdits` lets Claude
  write without prompting. *"In non-interactive mode with the -p flag, repeated blocks
  abort the session since there is no user to prompt."*
- **`--bare`** — *"reduce startup time by skipping auto-discovery of hooks, skills,
  plugins, MCP servers, auto memory, and CLAUDE.md… useful for CI and scripts where
  you need the same result on every machine."* Reproducibility: a teammate's local
  config won't leak into the run.

Scoping is the safety story. The fan-out recipe from best practices shows why:

```bash
for file in $(cat files.txt); do
  claude -p "Migrate $file from React to Vue. Return OK or FAIL." \
    --allowedTools "Edit,Bash(git commit *)"
done
```

*"The --allowedTools flag restricts what Claude can do, which matters when you're
running unattended."* Tool scoping is the unattended-run equivalent of the permission
prompts you'd see interactively.

### The GitHub Action

For repo automation, the `anthropics/claude-code-action@v1` action *"brings AI-powered
automation to your GitHub workflow. With a simple @claude mention in any PR or issue,
Claude can analyze your code, create pull requests, implement features, and fix
bugs."* A minimal workflow:

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
jobs:
  claude:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # Responds to @claude mentions in comments
```

Key facts: the action *"automatically detects whether to run in interactive mode
(responds to @claude mentions) or automation mode (runs immediately with a prompt)."*
You pass CLI flags through `claude_args` (*"--max-turns, --model, --allowedTools,
--append-system-prompt"*), and `prompt` for automation runs. Claude *"respects your
CLAUDE.md guidelines"* — your repo conventions apply in CI too.

### Authentication and secrets — the non-negotiable

Authentication is *"via ANTHROPIC\_API\_KEY secret"* — and the docs are blunt about
how: *"Never commit API keys directly to your repository… Always use GitHub Secrets
for API keys."* The pattern is always `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}`,
never a literal key in the YAML. For headless CI without a browser, generate a
long-lived token with `claude setup-token` and pass it via the
`CLAUDE_CODE_OAUTH_TOKEN` environment variable. On the direct Claude API path, that
key *is* the secret you store. Enterprises can instead route through **Amazon Bedrock
or Google Vertex AI** with OIDC (a Bedrock/Vertex-only alternative, not available for
the direct API) — *"OIDC is more secure… because credentials are temporary and
automatically rotated."*

The other guardrails from the security guidance: *"Limit action permissions to only
what's necessary"* and *"Review Claude's suggestions before merging"* — automation
proposes; a human still gates the merge.

## Worked example: a PR typo-linter step

You want every PR diff checked for typos automatically, cheaply, and safely.

```json
{
  "scripts": {
    "lint:claude": "git diff main | claude -p \"you are a typo linter. for each typo in this diff, report filename:line then the issue. return nothing else.\""
  }
}
```

Why each choice:

- **Pipe the diff in** rather than letting Claude run git: *"Piping the diff means
  Claude doesn't need Bash permission to read it"* — least privilege by construction.
- **`-p`** for a one-shot, sessionless run that exits with the result on stdout.
- **A tightly scoped prompt** ("return nothing else") so the output is parseable.
- For the GitHub-event version, wire the same idea into `claude-code-action` triggered
  on `pull_request`, with `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` and a
  scoped `claude_args: "--max-turns 5"`. The key lives in secrets; the run is bounded;
  a human still reviews the merge.

Every decision traces to the task: **headless `-p`** for the pipeline, **least-privilege
tool/permission scoping** because it's unattended, **secrets (never literals)** for
auth, and a **parseable output** contract.

## Anti-patterns & pitfalls

**Hard-coding the API key in the workflow file.** *"Never commit API keys directly to
your repository."* A literal key in YAML leaks to everyone with repo read access and
to forks. Always `${{ secrets.ANTHROPIC_API_KEY }}` (or OIDC to Bedrock/Vertex). This
is *the* CI anti-pattern this task statement tests.

**Running unattended with unbounded permissions.** No human is there to approve, so a
broad `bypassPermissions` or no `--allowedTools` lets an unattended run do anything.
Scope tools to exactly what the job needs (`--allowedTools`), or use `dontAsk` so
anything not pre-approved is denied rather than silently run.

**Expecting `-p` to pause for input.** Non-interactive means no prompts; *"repeated
blocks abort the session since there is no user to prompt."* Designing a CI step that
relies on a mid-run approval will just abort. Pre-authorize instead.

**Auto-merging Claude's output.** Automation *proposes*; the docs say *"Review
Claude's suggestions before merging."* Wiring the Action to merge its own PRs removes
the human gate that keeps a bad change out of `main`.

**Non-reproducible runs from ambient config.** Without `--bare`, `claude -p` loads
whatever hooks/MCP/CLAUDE.md happen to be present, so results differ across machines.
For CI that must be deterministic, use `--bare` and pass context explicitly.

## Exam focus

CCAF 3.6 rewards knowing both surfaces: **headless `claude -p`** (with
`--output-format`, `--allowedTools`, `--permission-mode dontAsk`, `--bare`) for
scripts/pipelines, and the **`claude-code-action`** GitHub Action (@claude triggers,
`claude_args`, auto interactive/automation detection). The "Anthropic way" emphasis is
**security**: API keys live in **secrets, never in the file** (or OIDC to
Bedrock/Vertex), permissions are **scoped down** for unattended runs, and a **human
reviews before merge**. The headline distractor is a hard-coded key; the runner-up is
unbounded permissions in an unattended job.

## References & further reading

- [GitHub Actions](https://code.claude.com/docs/en/github-actions) — the action,
  @claude triggers, `claude_args`, API-key secrets, and Bedrock/Vertex OIDC.
- [Run Claude Code programmatically (headless)](https://code.claude.com/docs/en/headless)
  — `claude -p`, output formats, `--allowedTools`, permission modes, `--bare`, and
  fan-out.
- [Best practices](https://code.claude.com/docs/en/best-practices) — non-interactive
  mode, scoping permissions for unattended runs, and parallel invocations.

## Exam coverage

- **CCAF** — Domain 3 (Claude Code & Configuration), Task Statement 3.6: Integrate
  Claude Code into CI/CD pipelines.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
