---
chapter: "3.2"
slug: "coordinator-subagent"
title: "Coordinator and subagent orchestration"
module: "module-3-agentic-core"
sequence: 9
references:
  - title: "Agent SDK — Subagents in the SDK"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "Coordinator spawns subagents, context isolation, what subagents inherit, AgentDefinition"
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs
    covers: "The loop the coordinator runs; subagents keep their work out of the parent's context"
---

# Coordinator and subagent orchestration

## Overview

A single agent with one context window can only hold so much before it starts to thrash. The fix is to split the work: a **coordinator** agent decomposes a task, hands focused pieces to **subagents**, and stitches their results back together. The exam describes this as **hub-and-spoke** — "a coordinator agent manages all inter-subagent communication, error handling, and information routing" (CCA-F Domain 1, Task Statement 1.2). The coordinator is the hub; subagents are spokes that never talk to each other directly.

There are two reasons this pattern wins, and both are about *context*. First, each subagent "runs in its own fresh conversation. Intermediate tool calls and results stay inside the subagent; only its final message returns to the parent" ([Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). A research subagent can read forty files and the coordinator only ever sees the three-sentence summary — the forty files never enter the coordinator's context. Second, because the coordinator owns all routing, you get one place for observability, error handling, and control.

This builds directly on the previous chapter (3.1, Agentic loops). A coordinator *is* an agentic loop — the same `stop_reason` loop — except its "tools" are subagents. When the coordinator decides it needs a researcher, it emits a tool call; you spawn the subagent, return its result, and the loop continues until the coordinator produces its synthesis. Keep that mental model: **orchestration is an agentic loop whose tools are other agents.**

## How it works

### The coordinator owns decomposition and routing

The coordinator's job is to look at the incoming request and decide *which* subagents to invoke and *what* to ask each one. The exam is explicit that this is a judgment call based on the query, not a fixed pipeline: design "coordinator agents that analyze query requirements and dynamically select which subagents to invoke rather than always routing through the full pipeline." A simple lookup might need one subagent; a broad research question might fan out to five. Routing everything through the coordinator is what gives you "observability, consistent error handling, and controlled information flow."

In the Agent SDK this is first-class: you declare subagents with the `agents` parameter, and "Claude determines whether to invoke them based on each subagent's `description` field" ([Agent SDK — subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Each subagent is an `AgentDefinition` with at least a `description` (when to use it) and a `prompt` (its specialized instructions), plus optional `tools` restrictions and a `model` override:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob", "Agent"],   # 'Agent' lets the coordinator spawn subagents
    agents={
        "researcher": AgentDefinition(
            description="Gathers facts from sources. Use for open-ended research subtasks.",
            prompt="You are a research specialist. Find and summarize relevant facts concisely.",
            tools=["Read", "Grep", "Glob", "WebSearch"],   # restrict what each spoke can do
        ),
        "synthesizer": AgentDefinition(
            description="Combines findings into a final answer. Use to aggregate research results.",
            prompt="You merge findings from multiple sources into one coherent, cited answer.",
        ),
    },
)
```

The coordinator invokes these through the built-in **Agent tool** — which is why `"Agent"` must be in `allowed_tools` for delegation to auto-approve. (The next chapter, 3.3, goes deeper on the invocation mechanics; here we care about the *pattern*.)

### Subagents start with a blank slate

This is the single most-tested fact here: **subagents do not inherit the coordinator's conversation history.** A subagent's context "starts fresh (no parent conversation)… The only channel from parent to subagent is the Agent tool's prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt" ([Agent SDK — what subagents inherit](https://code.claude.com/docs/en/agent-sdk/subagents#what-subagents-inherit)). A subagent *does* get its own system prompt and the project `CLAUDE.md`; it does **not** get the parent's history, the parent's system prompt, or another subagent's results unless you put them in the prompt.

The practical consequence: if the synthesizer needs the researcher's findings, the *coordinator* must pass those findings into the synthesizer's prompt. Subagents can't reach across to each other — and structurally they can't even try, because "subagents cannot spawn their own subagents." The hub-and-spoke shape is enforced by the runtime, not just by convention.

### The coordinator as a loop

Strip away the SDK and the pattern is the agentic loop from chapter 3.1 with subagents as tools. The coordinator calls the model with a set of "subagent tools"; when the model asks for one, you run that subagent **in isolation** — handing it only the task string the coordinator composed — and feed the result back:

```python
def run_coordinator(client, query, subagent_tools, spawn_subagent, safety_cap=25):
    messages = [{"role": "user", "content": query}]
    for _ in range(safety_cap):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=subagent_tools,          # each tool is a subagent the coordinator may invoke
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return response                # coordinator's synthesized answer

        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Isolated context: the subagent receives ONLY this task string,
                    # never the coordinator's `messages`.
                    result = spawn_subagent(block.name, block.input["task"])
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": results})
```

Notice `spawn_subagent(block.name, block.input["task"])`. The coordinator decides *what* each subagent is asked (`block.input["task"]`), and the subagent gets nothing else. That one line is the whole pattern: dynamic selection (the model picks `block.name`), explicit context passing (only `task`), and routing through the hub (the coordinator owns the dispatch).

## Worked example

Here's the loop wired to two concrete subagents, each spawned in isolation. The subagents are plain callables for the exercise; in production they'd be `AgentDefinition`s invoked via the Agent tool (or nested `query()` calls).

```python
import anthropic

RESEARCHER = {
    "name": "researcher",
    "description": "Researches a focused subtopic and returns a short factual summary. "
                   "Invoke once per distinct subtopic; do not use for final synthesis.",
    "input_schema": {
        "type": "object",
        "properties": {"task": {"type": "string", "description": "The specific subtopic to research."}},
        "required": ["task"],
    },
}
SYNTHESIZER = {
    "name": "synthesizer",
    "description": "Merges research findings into one cited answer. Pass the findings in the task.",
    "input_schema": {
        "type": "object",
        "properties": {"task": {"type": "string", "description": "Findings to merge, plus the original question."}},
        "required": ["task"],
    },
}

def spawn_subagent(name, task):
    """Run a subagent in ISOLATED context. It receives only `task` — no parent history."""
    sub = anthropic.Anthropic()
    prompts = {
        "researcher": "You are a research specialist. Summarize the key facts concisely.",
        "synthesizer": "You merge findings into one coherent, cited answer.",
    }
    resp = sub.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=prompts[name],                       # the subagent's OWN instructions
        messages=[{"role": "user", "content": task}],  # the ONLY context it gets
    )
    return "".join(b.text for b in resp.content if b.type == "text")

client = anthropic.Anthropic()
final = run_coordinator(
    client,
    "Compare the tradeoffs of REST vs gRPC for internal microservices.",
    [RESEARCHER, SYNTHESIZER],
    spawn_subagent,
)
```

The coordinator might call `researcher` twice (once for REST, once for gRPC), then `synthesizer` with both findings — or, for a trivial query, answer directly with no subagents at all. That choice is the coordinator's, made per query.

## Anti-patterns & pitfalls

The exam guide's knowledge and skills for this task statement (CCAF 1.2) map to four wrong patterns. Each one breaks the hub-and-spoke contract:

1. **Subagents communicating directly (peer-to-peer).** Wiring one subagent's output straight into another, or letting subagents call each other, instead of "routing all subagent communication through the coordinator." This destroys observability and consistent error handling — and the runtime forbids it anyway, since "subagents cannot spawn their own subagents." If the synthesizer needs the researcher's findings, the *coordinator* passes them.
2. **Always running the full pipeline.** Hardcoding "research → analyze → synthesize, every time" regardless of the request. The exam wants a coordinator that "analyze[s] query requirements and dynamically select[s] which subagents to invoke rather than always routing through the full pipeline." A fixed pipeline is a decision tree wearing an orchestrator costume — the same mistake the agentic-loop lesson (chapter 3.1) warns about, one level up.
3. **Assuming subagents inherit context.** Spawning a subagent with a vague prompt and expecting it to "remember" the conversation. It can't: it starts fresh and sees only the prompt string you pass. Forgetting to include the findings, file paths, or constraints the subagent needs is the most common cause of a subagent that "ignores" what the coordinator knows.
4. **Bad decomposition — too narrow or too overlapping.** The guide flags "risks of overly narrow task decomposition… leading to incomplete coverage of broad research topics." Carve the work so subagents cover the whole question without redundant overlap — "partition… research scope across subagents to minimize duplication (e.g., assigning distinct subtopics or source types to each agent)."

The Anthropic-prescribed shape is unambiguous: **hub-and-spoke, isolated subagent context, explicit prompts, dynamic selection.** Peer-to-peer graphs, shared global memory between subagents, and fixed pipelines are wrong answers on this exam, not stylistic alternatives.

## Exam focus

This task statement is the backbone of **Scenario 3 (Multi-Agent Research System)** — coordinator decomposes a research question, fans out to research subagents over distinct subtopics, and runs iterative refinement until coverage is sufficient. It also shows up in **Scenario 1 (Customer Support Resolution Agent)** when a support agent delegates a specialized lookup. Expect distractors that *sound* collaborative: subagents messaging each other, a shared memory store all agents read and write, or a rigid always-on pipeline. The correct answer routes everything through the coordinator and passes context explicitly.

## References & further reading

- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — how a coordinator spawns subagents, the "what subagents inherit" table, and the full `AgentDefinition` configuration. The primary reference for this lesson.
- [Agent SDK — How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) — the loop the coordinator runs, and why subagents keep their intermediate work out of the parent's context window.

## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
