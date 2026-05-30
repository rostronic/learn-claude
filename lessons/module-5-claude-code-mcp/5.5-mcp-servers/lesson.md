---
chapter: "5.5"
slug: "mcp-servers"
title: "Integrating MCP servers"
module: "module-5-claude-code-mcp"
sequence: 20
references:
  - title: "Claude Code — Connect Claude Code to tools via MCP"
    url: "https://code.claude.com/docs/en/mcp"
    type: official_docs
    covers: "claude mcp add, transports, scopes, .mcp.json, OAuth, resources, prompts, trust"
  - title: "Claude Code — Security (prompt injection)"
    url: "https://code.claude.com/docs/en/security"
    type: official_docs
    covers: "Trust and prompt-injection risk from servers that fetch external content"
  - title: "Model Context Protocol — Introduction"
    url: "https://modelcontextprotocol.io/introduction"
    type: official_docs
    covers: "What MCP is (open standard for AI-tool integration)"
---

# Integrating MCP servers

## Overview

The Model Context Protocol (MCP) is *"an open source standard for AI-tool
integrations"* that lets Claude Code *"connect to hundreds of external tools and
data sources… your tools, databases, and APIs"*
([MCP docs](https://code.claude.com/docs/en/mcp)). Connect a server and Claude can
read and act on that system directly — implement a Jira issue, query Postgres, pull
a Figma design — *"instead of working from what you paste."*

CCAF 2.4 is about **integrating** servers correctly: adding them with the right
**transport**, choosing the right **scope** (and who the config is shared with),
authenticating, and — the part the exam treats as load-bearing — doing it
**safely**, because a server that fetches external content is a prompt-injection
surface. This lesson teaches the mechanics and the judgment around them.

## How it works

### Adding a server and choosing a transport

You add servers with `claude mcp add`, picking a transport:

```bash
# Remote HTTP server (recommended for cloud services)
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Local stdio server (a local process)
claude mcp add --transport stdio --env AIRTABLE_API_KEY=KEY airtable \
  -- npx -y airtable-mcp-server
```

The transports: **HTTP** (*"the recommended option for connecting to remote MCP
servers"*), **stdio** (*"local processes… ideal for tools that need direct system
access or custom scripts"*), and **SSE** — which is **deprecated**: *"Use HTTP
servers instead, where available."* Knowing HTTP-over-SSE is a likely exam detail.

### Scopes — and who the config is shared with

A server is configured at one of three scopes, and the scope decides *where it
loads* and *whether your team gets it*:

| Scope | Loads in | Shared with team | Stored in |
|---|---|---|---|
| **local** (default) | Current project only | No | `~/.claude.json` |
| **project** | Current project only | **Yes**, via version control | `.mcp.json` in project root |
| **user** | All your projects | No | `~/.claude.json` |

`--scope project` writes a checked-in `.mcp.json` so *"all team members have access
to the same MCP tools."* When the same server name is defined at more than one
scope, *"Claude Code connects to it once, using the definition from the
highest-precedence source… fields are not merged across scopes."* The order is
**local → project → user** (then plugin servers, then claude.ai connectors).

### The `.mcp.json` file and env-var expansion

A project-scoped server lands in `.mcp.json`:

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": { "Authorization": "Bearer ${API_KEY}" }
    }
  }
}
```

Because `.mcp.json` is shared, it supports environment-variable expansion so
machine-specific paths and **secrets stay out of the file**: *"`${VAR}` expands to
the value of environment variable VAR"* and *"`${VAR:-default}` expands to VAR if
set, otherwise uses default."* Critically: *"If a required environment variable is
not set and has no default value, Claude Code will fail to parse the config."* That
fail-closed behavior is deliberate — a missing secret errors loudly rather than
connecting with a blank credential.

### Authentication

Many remote servers need OAuth. Claude Code marks a server as needing auth when it
returns `401`/`403`, and you complete the flow with the `/mcp` command: *"Then
follow the steps in your browser to login."* Tokens are stored securely and
refreshed automatically. For static tokens you can pass a `--header
"Authorization: Bearer …"` instead.

### Using what a server exposes

A connected server gives Claude three things:

- **Tools** — Claude calls them like any tool. (By default MCP tools are
  *deferred* via tool search so adding servers barely costs context until a tool is
  needed.)
- **Resources** — reference with `@`: *"Use the format @server:protocol://resource/path"*,
  e.g. `@github:issue://123` or `@postgres:schema://users`.
- **Prompts** — surface as commands: *"MCP prompts appear with the format
  /mcp__servername__promptname"*, e.g. `/mcp__github__pr_review 456`.

### Trust — the safety gate

This is the part CCAF emphasizes. The docs warn directly: *"Verify you trust each
server before connecting it. Servers that fetch external content can expose you to
prompt injection risk."* Two consequences:

1. **Project-scoped servers are approved, not auto-trusted.** *"For security
   reasons, Claude Code prompts for approval before using project-scoped servers
   from .mcp.json files."* So pulling a repo with a `.mcp.json` doesn't silently
   connect you to its servers — you approve first.
2. **External content is an injection vector.** A server that pulls in issues, web
   pages, or tickets can carry instructions hostile to you; treat its output as
   untrusted data, not as commands. (Domain 5 covers provenance and review in
   depth.)

## Worked example: a team Postgres server, safely

Your team wants Claude to answer questions against a read-only analytics database,
shared with everyone on the repo.

1. **Add it at project scope** so it's checked in and the whole team gets it:

   ```bash
   claude mcp add --transport stdio --scope project db \
     -- npx -y @bytebase/dbhub --dsn "${ANALYTICS_DSN}"
   ```

   This writes `.mcp.json` with a `${ANALYTICS_DSN}` placeholder — the **DSN itself
   never enters the committed file**; each developer sets the env var locally. If
   it's unset, the config fails to parse rather than connecting blind.

2. **Approve on first use.** Because it's project-scoped, each teammate gets the
   approval prompt the first time — the trust gate, working as designed.

3. **Authenticate / scope to read-only.** Use a read-only DSN so even a worst-case
   prompt-injection can't mutate data. Least privilege is the mitigation; the
   protocol won't add it for you.

4. **Use it.** Ask questions naturally ("what's our revenue this month?") and
   reference schema resources with `@db:schema://orders`.

The integration choices all trace to the task: **project** scope for team sharing,
**env-var expansion** to keep the secret out of git, the **approval** gate for
trust, and **least-privilege credentials** because a tool that touches your data is
a security boundary.

## Anti-patterns & pitfalls

**Committing secrets into `.mcp.json`.** The file is shared in version control.
Hard-coding an API key or DSN leaks it to everyone with repo access. Use `${VAR}` /
`${VAR:-default}` expansion and keep the secret in the environment. This is the
canonical MCP-integration mistake.

**Connecting an untrusted server without thinking about injection.** *"Servers that
fetch external content can expose you to prompt injection risk."* Adding a random
third-party server — especially one that reads web pages, issues, or email — without
trusting it (and without treating its output as untrusted data) is the security
anti-pattern this task statement targets. Verify the server; prefer least-privilege
credentials.

**Reaching for the deprecated SSE transport.** SSE is deprecated; use HTTP for
remote servers. Picking SSE for a new integration is a dated-knowledge tell.

**Assuming a project `.mcp.json` auto-connects on checkout.** It doesn't — Claude
Code prompts for approval before using project-scoped servers. Expecting silent
activation (or being surprised by the prompt) misreads the trust model.

**Granting broad credentials when read-only would do.** If Claude only needs to
*query* a database or *read* issues, give it a read-only credential. The protocol
gives the model whatever the token allows; scope the token, not just the prompt.

## Exam focus

CCAF 2.4 rewards the integration mechanics — `claude mcp add` with the right
**transport** (HTTP over deprecated SSE; stdio for local), the three **scopes** and
that **project** scope means a checked-in `.mcp.json` shared with the team, env-var
expansion to keep secrets out of that file, `/mcp` for OAuth, and `@server:…` /
`/mcp__server__prompt` to use resources and prompts. The "Anthropic way" emphasis is
**trust and least privilege**: project servers require approval, external-content
servers are an injection surface, and credentials should be scoped. Reliable
distractors: hard-coding a secret in `.mcp.json`, picking SSE, and assuming silent
auto-connect.

## References & further reading

- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp) — the
  full reference: `claude mcp add`, transports, scopes/precedence, `.mcp.json` and
  env expansion, OAuth, resources, and prompts.
- [Security — protect against prompt injection](https://code.claude.com/docs/en/security)
  — why a server that fetches external content is a risk surface.
- [Model Context Protocol — Introduction](https://modelcontextprotocol.io/introduction)
  — the open standard MCP implements.

## Exam coverage

- **CCAF** — Domain 2 (Tools & MCP), Task Statement 2.4: Integrate MCP servers into
  Claude Code and agent workflows.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
