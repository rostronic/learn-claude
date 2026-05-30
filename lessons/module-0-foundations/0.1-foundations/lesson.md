---
chapter: "0.1"
slug: "foundations"
title: "Foundations: the four technologies"
module: "module-0-foundations"
sequence: 1
references:
  - title: "Using the Messages API"
    url: "https://platform.claude.com/docs/en/build-with-claude/working-with-messages"
    type: official_docs
    covers: "The Messages API: direct, stateless model access; request/response shape; stop_reason"
  - title: "Agent SDK overview"
    url: "https://code.claude.com/docs/en/agent-sdk/overview"
    type: official_docs
    covers: "What the Claude Agent SDK is; the built-in agent loop, tools, and context management; how it compares to the raw Client SDK"
  - title: "Claude Code overview"
    url: "https://code.claude.com/docs/en/overview"
    type: official_docs
    covers: "What Claude Code is: an agentic coding tool across terminal, IDE, desktop, and browser"
  - title: "Connect Claude Code to tools via MCP"
    url: "https://code.claude.com/docs/en/mcp"
    type: official_docs
    covers: "MCP as the open standard for connecting Claude to external tools and data sources"
---

# Foundations: the four technologies

## Overview

This is the first chapter of the learning path, and it exists to give you a map. Almost everything Anthropic ships for builders is one of four things, and the rest of this course assumes you can tell them apart:

- the **Messages API** — direct, stateless access to the model;
- the **Claude Agent SDK** — a library that runs the agent loop for you;
- **Claude Code** — the agentic coding tool you drive in a terminal or IDE;
- the **Model Context Protocol (MCP)** — the open standard that plugs external tools and data into Claude.

These are not four competing products you choose between once. They're **layers**. The Messages API is at the bottom; the Agent SDK runs the agent loop on top of it; Claude Code is that same engine packaged as a developer tool; MCP runs alongside all of them as a connector. Knowing where each one sits — and therefore which one a given task actually calls for — is the orientation the rest of the course builds on. This chapter is exam-agnostic: no task statement, just the lay of the land.

## How it works

### The Messages API — direct model access

The Messages API is the foundation: you send a request containing the conversation so far, and the model returns one response. Anthropic describes it as "direct model prompting access," best for "custom agent loops and fine-grained control" ([Using the Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)). A minimal call is exactly what you'd expect:

```python
import anthropic

message = anthropic.Anthropic().messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
)
print(message.stop_reason)   # e.g. "end_turn"
```

Two properties define this layer. First, it's **stateless**: "you always send the full conversational history to the API" ([Using the Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)) — the API remembers nothing between calls, so *you* own the conversation. Second, there is **no built-in loop**: if you want the model to call a tool, see the result, and decide again, you write that cycle yourself, branching on `response.stop_reason`. (That hand-built loop is exactly what Chapter 3.1 teaches.)

Reach for the raw Messages API when a single model call — or a loop simple enough that you want to own every line of it — does the job: classification, extraction, summarization, a one-shot generation. You don't need a framework to send one prompt and read one response.

### The Claude Agent SDK — the loop, run for you

The Agent SDK is the next layer up. Instead of writing the call-tool-feed-result-repeat cycle by hand, you hand the SDK a prompt and a set of allowed tools and it runs the loop. It "gives you the same tools, agent loop, and context management that power Claude Code, programmable in Python and TypeScript" ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)).

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
    ):
        print(message)   # Claude reads the file, finds the bug, edits it

asyncio.run(main())
```

The official docs draw the line between this and the raw API precisely. With the Client SDK (the `anthropic` package and the Messages API beneath it) "you implement a tool loop"; with the Agent SDK "Claude handles it" ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)):

```python
# Client SDK: you implement the tool loop
response = client.messages.create(...)
while response.stop_reason == "tool_use":
    result = your_tool_executor(response.tool_use)
    response = client.messages.create(tool_result=result, **params)

# Agent SDK: Claude handles tools autonomously
async for message in query(prompt="Fix the bug in auth.py"):
    print(message)
```

Reach for the Agent SDK when you're embedding an **autonomous, multi-step agent inside your own application** — a backend service that triages tickets, a CI job that edits code, a research agent — and you want Claude's built-in tools, the loop, and context management without reimplementing them. It runs the agent loop inside your own process ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)).

### Claude Code — the agentic harness

Claude Code is the product form of that same engine. It "is an agentic coding tool that reads your codebase, edits files, runs commands, and integrates with your development tools," available "in your terminal, IDE, desktop app, and browser" ([Claude Code overview](https://code.claude.com/docs/en/overview)). Where the Agent SDK is a library you call, Claude Code is a harness you drive:

```bash
cd your-project
claude "write tests for the auth module, run them, and fix any failures"
```

The relationship is explicit in the docs: the Agent SDK lets you "build production AI agents with Claude Code as a library," exposing "the same tools, agent loop, and context management that power Claude Code" ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)). Same engine; the SDK is the programmable form, Claude Code is the ready-to-use developer tool — and the two share configuration like `CLAUDE.md`, skills, and MCP servers.

Reach for Claude Code when **a developer is the one in the loop**: interactive coding in a terminal or IDE, one-off automation tasks, or — via GitHub Actions and the like — coding work in CI. (Modules 5 and 6 are largely about driving Claude Code well.)

### MCP — connecting tools and data

The Model Context Protocol is the odd one out: it isn't a layer in the stack, it's the **connector** that runs alongside it. Claude (whether through Claude Code or the Agent SDK) "can connect to hundreds of external tools and data sources through the Model Context Protocol (MCP), an open source standard for AI-tool integrations. MCP servers give Claude Code access to your tools, databases, and APIs" ([Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)).

```bash
# Give Claude Code access to an external system by adding its MCP server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

An MCP **server** exposes a system — Jira, Postgres, Sentry, your own internal API — as a set of tools; an MCP **client** (Claude Code, the Agent SDK, Claude.ai) consumes them. Reach for MCP when the need is **integration**: you want Claude to read or act on a system it can't reach out of the box, instead of you copying data into the prompt by hand. MCP is the answer to "how do I connect Claude to *X*," not to "how do I run an agent."

### How they relate

Put together, the four form a stack with a connector bolted across it:

| Technology | What it is | Reach for it when… |
|---|---|---|
| **Messages API** | Direct, stateless model access; you build any loop | One call (or a loop you want to own) suffices: classify, extract, summarize, generate |
| **Claude Agent SDK** | Runs the agent loop for you, in your process | You're embedding an autonomous multi-step agent in your own app/service |
| **Claude Code** | The agentic coding harness (terminal/IDE/desktop/web) | A developer is interactively coding, or automating coding work |
| **MCP** | Open standard connecting Claude to external tools/data | You need to connect Claude to a system (DB, tracker, API) |

The load-bearing mental model: **the Messages API is underneath, the Agent SDK runs the loop on top of it, Claude Code is that loop packaged as a developer tool, and MCP plugs tools into whichever of them you're using.** Climb the stack only as far as the task requires — and add MCP when, and only when, you need to reach an outside system.

## Worked example

The exercise turns that decision into code: a small, pure-logic recommender that, given the salient feature of a task, names the technology to reach for first. No API calls — just the decision tree from the table above, in priority order.

```python
TECHNOLOGIES = ("messages_api", "agent_sdk", "claude_code", "mcp")

def recommend_technology(task):
    """Given a task's signals, name the primary technology to reach for.

    `task` is a dict of boolean signals. Checked in priority order:
    the connection need and the human-in-the-loop need are more specific
    than "needs a loop," which is more specific than "one call will do."
    """
    if task.get("connect_external_system"):
        return "mcp"
    if task.get("interactive_coding"):
        return "claude_code"
    if task.get("needs_autonomous_loop"):
        return "agent_sdk"
    return "messages_api"   # the floor: a single call is enough
```

Walking a few tasks through it:

- `{"connect_external_system": True}` — "let Claude answer questions from our Postgres database." The need is integration, so the answer is **MCP**, regardless of which harness ultimately calls the tools.
- `{"interactive_coding": True}` — "help me refactor this module in my terminal." A developer is in the loop: **Claude Code**.
- `{"needs_autonomous_loop": True}` — "embed an agent in our backend that triages tickets with tools." A programmatic multi-step agent in your own process: the **Agent SDK**.
- `{}` — "classify this one support email into a category." No tools, no loop, no integration: the **Messages API** is the floor and it's enough.

The priority order matters because a real task can light up more than one signal — Claude Code itself *uses* MCP servers and *is* built on the SDK's loop. The recommender names the **primary** technology to start from; it doesn't pretend the four never combine. The crucial property, and the one the rubric grades, is the **last line**: when no special signal is set, the floor is `messages_api`. Defaulting that fallback to `agent_sdk` is the central mistake this chapter is here to prevent.

## Anti-patterns & pitfalls

1. **Reaching for the Agent SDK when the raw Messages API suffices.** The most common orientation error: a task is "an AI feature," so it must need an "agent framework." But a single classification or extraction call needs no loop, no tools, and no SDK — just `messages.create`. The Agent SDK earns its keep when there's an *autonomous multi-step loop* to run; for a one-shot prompt it's machinery you'll only have to maintain. Climb the stack only as far as the task requires. (In the exercise this is the graded anti-pattern: the recommender's fallback must be `messages_api`, never `agent_sdk`.)
2. **Confusing Claude Code (the product) with the Agent SDK (the library).** They share an engine, but they're not interchangeable answers. "A developer wants to refactor code in their terminal" is Claude Code. "We want to ship an agent inside our own service" is the Agent SDK. Naming the SDK when a human is interactively coding — or naming Claude Code when you mean an embedded programmatic agent — is picking the wrong form of the same engine.
3. **Treating MCP as an alternative to the SDK or the API.** MCP is a *connector*, not a runtime — it answers "how do I connect Claude to this system," not "how do I run an agent." You don't choose "MCP *instead of* the Agent SDK"; you run an agent (SDK or Claude Code) and *add* an MCP server when it needs to reach an external system. Framing them as either/or is a category error.
4. **Hand-writing the loop when the SDK already runs one.** The inverse of anti-pattern 1: if you *do* need an autonomous multi-step agent with file, command, and search tools, reimplementing the call-tool-feed-result cycle on the raw Messages API is reinventing what the Agent SDK gives you for free, including its tools and context management. Build the loop by hand to *learn* it (Chapter 3.1) or when you need total control; don't do it by default in production.

The thread through all four: **match the technology to the task's real shape, and climb no higher in the stack than you must.** A simple prompt wants the Messages API; an embedded agent wants the SDK; an interactive developer wants Claude Code; an external system wants MCP. Reaching for heavier machinery than the task needs is the mistake to avoid.

## References & further reading

- [Using the Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) — the foundational layer: direct, stateless model access, the request/response shape, and `stop_reason`. This is what everything else is built on.
- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) — what the Agent SDK is, the built-in agent loop and tools, and the explicit Client-SDK-vs-Agent-SDK comparison ("you implement a tool loop" vs. "Claude handles it").
- [Claude Code overview](https://code.claude.com/docs/en/overview) — what Claude Code is and the surfaces it runs on, plus how it relates to the Agent SDK ("build custom agents for your own workflows").
- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp) — MCP as the open standard for connecting Claude to external tools and data, and how to add a server.
