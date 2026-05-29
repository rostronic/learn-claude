---
chapter: "3.4"
slug: "tool-distribution"
title: "Distributing tools across agents & tool choice"
module: "module-3-agentic-core"
sequence: 11
references:
  - title: "Agent SDK — Subagents in the SDK"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Restricting a subagent's tools (the tools field); common tool combinations; tool restriction as safety"
  - title: "Define tools (tool_choice)"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use"
    type: official_docs
    covers: "tool_choice modes: auto / any / forced tool / none"
---

# Distributing tools across agents & tool choice

## Overview

Once you have multiple agents (chapters 3.2–3.3), a new design question appears: *which* tools does each agent get? The intuitive answer — "give every agent everything, just in case" — is wrong, and the exam is emphatic about why. Tool selection is a reasoning task, and "giving an agent access to too many tools (e.g., 18 instead of 4–5) degrades tool selection reliability by increasing decision complexity" (CCAF 2.3). Fewer, role-appropriate tools make an agent *more* reliable, not less capable.

This pairs with the `tool_choice` control from chapter 1.3: distributing tools decides *what an agent can reach*; `tool_choice` decides *whether and which* tool it must call on a given turn. Together they're how you keep a multi-agent system's tool use predictable.

## How it works

### Scope each agent's tools to its role

Give an agent only the tools its role needs. The Agent SDK makes this a first-class field: a subagent's `tools` array restricts what it can use, and "if omitted, inherits all tools" ([Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents)) — so omitting it is the over-provisioning trap. The docs frame restriction as a safety lever too: a read-only reviewer limited to `["Read", "Grep"]` "can analyze but never accidentally modify your documentation files." Two failure modes scoping prevents:

- **Decision overload.** 18 tools is 18 things to disambiguate every turn; 4–5 is a clean choice. Reliability drops as the menu grows.
- **Cross-specialization misuse.** "Agents with tools outside their specialization tend to misuse them (e.g., a synthesis agent attempting web searches)" (CCAF 2.3). If the synthesizer can't search, it can't mis-search.

When a specialized agent genuinely needs an occasional cross-role capability, give it a **scoped** version, not the general tool: "Providing scoped cross-role tools for high-frequency needs (e.g., a `verify_fact` tool for the synthesis agent) while routing complex cases through the coordinator." And prefer **constrained alternatives** to generic tools — "replacing `fetch_url` with `load_document` that validates document URLs" — so the tool itself can't be misused.

### Control the call with `tool_choice`

Distribution decides the menu; `tool_choice` decides the order. The three modes (same as chapter 1.3):

- **`"auto"`** — model may call a tool or answer in text.
- **`"any"`** — model must call *some* tool. Use it "to guarantee the model calls a tool rather than returning conversational text" (CCAF 2.3).
- **`{"type": "tool", "name": "extract_metadata"}`** — forces a *specific* tool. Use it to "ensure a specific tool is called first (e.g., forcing `extract_metadata` before enrichment tools), then processing subsequent steps in follow-up turns."

```python
# A scoped subagent: only the tools its role needs, plus a forced first step.
researcher = {
    "tools": ["Read", "Grep", "Glob", "WebSearch"],          # 4 role tools, not 18
}
synthesizer = {
    "tools": ["Read", "verify_fact"],                        # scoped cross-role tool, not raw WebSearch
}
# Force the metadata extraction before any enrichment runs:
tool_choice = {"type": "tool", "name": "extract_metadata"}
```

## Worked example

A helper that hands an agent exactly its role's tools — refusing to over-provision — plus the two `tool_choice` constructors:

```python
def build_agent_toolset(role, role_tools, max_tools=5):
    """role_tools: {role: [tool names]}. Returns the scoped list for `role`."""
    if role not in role_tools:
        raise KeyError(f"no tool scope defined for role {role!r}")
    tools = role_tools[role]
    if len(tools) > max_tools:
        raise ValueError(
            f"role {role!r} has {len(tools)} tools (> {max_tools}); too many tools "
            "degrades selection reliability — scope it down or split the role"
        )
    return list(tools)                       # a copy; never the shared registry

def tool_choice_any():
    return {"type": "any"}                   # must call a tool, model picks

def tool_choice_force(name):
    return {"type": "tool", "name": name}    # must call this specific tool

SCOPES = {
    "researcher": ["Read", "Grep", "Glob", "WebSearch"],
    "synthesizer": ["Read", "verify_fact"],
}
tools = build_agent_toolset("synthesizer", SCOPES)   # ['Read', 'verify_fact']
```

`build_agent_toolset` returns a *copy* of the role's scoped list and rejects an over-stuffed role outright — the cap is the guardrail against the 18-tool failure mode.

## Anti-patterns & pitfalls

1. **Giving every agent every tool.** Omitting the `tools` restriction (so the agent inherits all tools) or passing the full registry. More tools = worse selection. Scope to the role.
2. **Generic tools where a constrained one would do.** Handing an agent `fetch_url`/raw `WebSearch` when it only ever needs to load validated documents or verify a fact. Replace generic tools with constrained alternatives, or scope the capability.
3. **Cross-specialization tools with no guardrail.** Letting the synthesizer search the web "just in case" invites misuse; route complex cross-role needs through the coordinator instead, and give only narrow, high-frequency helpers directly.
4. **`tool_choice: "auto"` when a call is required.** If the turn must produce a tool call (extraction, a forced first step), `"auto"` lets the model answer in prose. Use `"any"` or force the specific tool.

The prescribed approach: **scope tools tightly to each agent's role, prefer constrained tools, route the rest through the coordinator, and use `tool_choice` to force calls when a turn requires one.**

## Exam focus

This is central to **CCAF Scenario 3 (Multi-Agent Research System)** — the research/synthesis split is the canonical example of scoped tool access (the synthesizer shouldn't search) — and **Scenario 4 (Developer Productivity)**. The distractor to reject is "give the agent more tools so it can handle more cases"; the exam's answer is fewer, role-scoped tools, with `tool_choice` to control the call.

## References & further reading

- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — the `tools` restriction field, the common tool-combinations table, and restriction as a safety lever.
- [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — the `tool_choice` modes (`auto` / `any` / forced tool / `none`).

## Exam coverage

- **CCAF** — Domain 2 (Tool Design & MCP Integration), Task Statement 2.3: Distribute tools appropriately across agents and configure tool choice.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
