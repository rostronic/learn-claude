---
chapter: "3.3"
slug: "subagent-invocation"
title: "Subagent invocation and context passing"
module: "module-3-agentic-core"
sequence: 10
references:
  - title: "Agent SDK — Subagents in the SDK"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Agent/Task tool, allowed_tools requirement, AgentDefinition fields, what subagents inherit, parallel invocation"
  - title: "Agent SDK — Work with sessions"
    url: "https://code.claude.com/docs/en/agent-sdk/sessions"
    type: official_docs
    covers: "Fork-based session management for exploring divergent approaches from a shared baseline"
---

# Subagent invocation and context passing

## Overview

The previous chapter (3.2, Coordinator and subagent orchestration) gave you the *pattern* — hub-and-spoke, isolated subagent context. This lesson is the *wiring*: how a coordinator actually spawns a subagent, what you must hand it (because it inherits nothing), how you configure each subagent type, and how you branch exploration without losing your baseline. Get these mechanics wrong and that elegant pattern silently fails — the coordinator can't delegate, or the subagent works from an empty context and produces confident nonsense.

The exam tests several mechanics here. Four are central — the **spawning tool** and the permission it requires, **explicit context passing** (subagents don't share memory), **`AgentDefinition`** configuration, and **fork-based sessions** for divergent exploration — plus two supporting skills: spawning subagents **in parallel** and writing **goal-driven coordinator prompts**. None of them is hard individually; the failures come from assuming the framework does something for you that it doesn't.

## How it works

### Spawning: the Task/Agent tool and the permission it needs

A coordinator spawns a subagent by calling a built-in tool — and that tool has to be allowed, or the call is denied. The exam guide names it the **Task tool** and states the requirement directly: "`allowedTools` must include `"Task"` for a coordinator to invoke subagents."

There's a naming wrinkle worth knowing, because the docs and the exam guide use different names. The tool "was renamed from `"Task"` to `"Agent"` in Claude Code v2.1.63. Current SDK releases emit `"Agent"` in `tool_use` blocks but still use `"Task"` in the `system:init` tools list and in `result.permission_denials[].tool_name`" ([Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents#detecting-subagent-invocation)). Practical upshot: the exam will say "Task"; real code should **allow and detect both names**. If you forget to include it in `allowed_tools`, delegation "fall[s] through to your `canUseTool` callback or, in `dontAsk` mode, [is] denied" — the coordinator just answers directly instead of delegating.

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob", "Agent"],  # "Agent" (a.k.a. "Task") enables spawning
    agents={...},
)
```

### Context passing: subagents start empty, so say everything

This is the rule the exam hammers: "subagent context must be explicitly provided in the prompt—subagents do not automatically inherit parent context or share memory between invocations." A subagent's only inbound channel is the Agent tool's prompt string. It does not see the coordinator's conversation, another subagent's results, or anything a *previous* invocation of the same subagent learned — there is no shared memory across invocations.

So when the coordinator hands work to a synthesis subagent, it must **include the complete findings from prior agents directly in that subagent's prompt** — e.g., passing the web-search results and document-analysis outputs into the synthesizer's prompt. And it should pass them as **structured data that separates content from metadata** (source URLs, document names, page numbers) so attribution survives the handoff:

```python
task = f"""Synthesize an answer to: {question}

Findings (preserve attribution to each source):
{json.dumps(findings, indent=2)}
"""
# findings = [{"source": "https://...", "title": "...", "content": "..."}, ...]
```

Structured findings beat a flattened blob: the synthesizer can cite "per [title](source)" instead of guessing which claim came from where.

### AgentDefinition: configuring each subagent type

Each subagent type is declared with an `AgentDefinition`. The fields the exam cares about are the description, the system prompt, and the tool restrictions: `description` (natural-language "when to use this agent" — Claude routes on it), `prompt` (the subagent's own system prompt and expertise), and `tools` (the allowed tool names; "if omitted, inherits all tools") ([Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Restricting tools is a safety lever — a `doc-reviewer` limited to `["Read", "Grep"]` can analyze but "never accidentally modify your documentation files."

```python
agents={
    "researcher": AgentDefinition(
        description="Researches one focused subtopic. Use per distinct subtopic.",
        prompt="You are a research specialist. Return concise, sourced facts.",
        tools=["Read", "Grep", "Glob", "WebSearch"],   # restricted: no Edit/Write/Bash
    ),
}
```

### Parallel spawning: many Task calls in one turn

When subtasks are independent, the coordinator should **emit multiple Task tool calls in a single response** rather than spreading them across separate turns. The runtime can then run them concurrently — "multiple subagents can run concurrently, dramatically speeding up complex workflows." One turn with three `tool_use` blocks fans out; three sequential turns serialize the same work.

### Fork-based sessions: branch without losing your baseline

Sometimes you want to explore two directions from the same starting analysis. **Forking** does exactly that: it "creates a new session that starts with a copy of the original's history but diverges from that point. The fork gets its own session ID; the original's ID and history stay unchanged" ([Agent SDK — sessions](https://code.claude.com/docs/en/agent-sdk/sessions#fork-to-explore-alternatives)). You set it with `fork_session=True` alongside `resume`:

```python
# Branch from an analyzed baseline into a new approach; original is untouched
async for message in query(
    prompt="Instead of JWT, explore OAuth2 for the auth module",
    options=ClaudeAgentOptions(resume=session_id, fork_session=True),
):
    ...
```

This is how you run "what if we tried X instead?" from a shared baseline without rerunning the expensive analysis or contaminating the original thread.

### Coordinator prompts: goals, not scripts

One more skill the guide calls out: write coordinator prompts that "specify research goals and quality criteria rather than step-by-step procedural instructions, to enable subagent adaptability." Tell a subagent *what good looks like* ("find the three most load-bearing tradeoffs, with sources") and let it adapt; don't hand it a rigid procedure that breaks the moment reality differs from your script.

## Worked example

A small helper that builds a single subagent invocation correctly: it refuses to spawn if the Task/Agent tool isn't allowed, looks up the subagent's `AgentDefinition`, and composes a prompt with **explicit, attributed** context.

```python
import json

SPAWN_TOOLS = {"Task", "Agent"}   # accept both names (exam says Task; current SDK emits Agent)

def build_subagent_invocation(agent_name, registry, allowed_tools, task, prior_findings):
    # 1. Spawning must be permitted.
    if not (SPAWN_TOOLS & set(allowed_tools)):
        raise PermissionError("coordinator can't spawn subagents: add 'Task'/'Agent' to allowed_tools")

    # 2. Look up this subagent type's AgentDefinition.
    if agent_name not in registry:
        raise KeyError(f"no subagent defined named {agent_name!r}")
    agent = registry[agent_name]

    # 3. Pass context EXPLICITLY — the subagent inherits nothing. Keep attribution.
    findings_block = json.dumps(prior_findings, indent=2)
    prompt = f"{task}\n\nContext (cite these sources):\n{findings_block}"

    return {
        "name": agent_name,
        "system": agent["prompt"],          # the subagent's own instructions
        "prompt": prompt,                    # the only context it will ever see
        "tools": agent.get("tools"),         # None => inherits all tools
    }
```

The coordinator composes one of these per subagent it wants to spawn, emitting them together for parallel fan-out. Nothing about the coordinator's own conversation leaks in — only the `task` and the `prior_findings` you chose to pass.

## Anti-patterns & pitfalls

1. **Spawning without the permission.** Building beautiful `AgentDefinition`s but leaving `"Task"`/`"Agent"` out of `allowed_tools`. The coordinator then can't delegate — invocations are denied or fall through — and it quietly answers alone. Always allow (and detect) both tool names.
2. **Relying on implicit or shared context.** Spawning with a thin prompt and expecting the subagent to "remember" the conversation or read another subagent's results. It can't: no inheritance, no shared memory between invocations. Forgetting to inline the prior findings is the #1 cause of a subagent that ignores what the coordinator knows.
3. **Losing attribution in the handoff.** Flattening findings into one undifferentiated blob, so the synthesizer can't say which claim came from which source. Pass structured findings (content separated from source/title/page metadata).
4. **Serial spawning of parallel work.** Emitting one Task call per turn for independent subtasks instead of multiple Task calls in a single response — throwing away the concurrency the runtime would give you for free.
5. **Procedural coordinator prompts.** Scripting a subagent step-by-step instead of stating goals and quality criteria. Rigid scripts can't adapt; goal-driven prompts can.

The prescribed configuration is unambiguous: **allow the spawning tool, pass complete context explicitly and with attribution, restrict each subagent's tools to what it needs, fan out in one turn, and fork to branch.** Implicit inheritance, shared global memory, and rigid procedural scripts are wrong answers on this exam.

## Exam focus

This is the most mechanical task statement in Domain 1, and it powers **Scenario 3 (Multi-Agent Research System)** end-to-end: the coordinator spawns research subagents in parallel (multiple Task calls per turn), passes their structured findings into a synthesis subagent's prompt, and forks the session to explore a divergent research angle from the same baseline. Expect distractors built on the things that *feel* convenient but the framework doesn't do: a shared memory store every agent reads/writes, subagents that "inherit" the coordinator's context, or sequential spawning. The correct answer always passes context explicitly and allows the Task/Agent tool.

## References & further reading

- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — the Agent/Task tool and `allowed_tools` requirement, the `AgentDefinition` fields, the "what subagents inherit" table, parallel invocation, and the Task→Agent rename note. Primary reference.
- [Agent SDK — Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) — `resume` vs `fork`, and how forking branches a conversation from a shared baseline while leaving the original untouched.

## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.3: Configure subagent invocation, context passing, and spawning.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
