---
chapter: "4.3"
slug: "task-decomposition"
title: "Task decomposition strategies"
module: "module-4-workflows-state"
sequence: 14
references:
  - title: "Agent SDK — Subagents in the SDK"
    url: "https://code.claude.com/docs/en/agent-sdk/subagents"
    type: official_docs
    covers: "AgentDefinition, context isolation, parallelization, tool restriction, the one-level (no nested subagents) rule, prompt-string handoff"
  - title: "Agent SDK — Dynamic workflows"
    url: "https://code.claude.com/docs/en/workflows"
    type: official_docs
    covers: "Orchestrating dozens-to-hundreds of agents from a script when turn-by-turn subagent delegation isn't enough"
---

# Task decomposition strategies

## Overview

A complex task is rarely best handled by one agent grinding through everything in a single context. The better design is to **decompose** it: split the work into focused subtasks, hand each to a subagent scoped to exactly what it needs, run the independent ones in parallel, and order the dependent ones. Decomposition is what turns "review this PR" from one sprawling conversation into a style check, a security scan, and a test run happening at once, followed by a synthesis that reads their results.

The payoff is three things the Agent SDK names directly. **Context isolation:** each subagent "runs in its own fresh conversation," and "only its final message returns to the parent," so a finder can read dozens of files "without any of that content accumulating in the main conversation" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). **Parallelization:** "multiple subagents can run concurrently, dramatically speeding up complex workflows" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). **Least privilege:** each subagent can be "limited to specific tools, reducing the risk of unintended actions" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Good decomposition is the planning discipline that earns all three. This lesson is about *how to plan the split* — and the hard constraints that bound it.

## How it works

In the SDK you define subagents with the `agents` option, mapping a name to an `AgentDefinition` ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)):

```python
from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob", "Agent"],   # include Agent to auto-approve delegation
    agents={
        "security-scanner": AgentDefinition(
            description="Finds security vulnerabilities in changed files.",
            prompt="You are a security reviewer. Report injection, authz, and secret-handling issues.",
            tools=["Read", "Grep", "Glob"],             # read-only: cannot modify or execute
        ),
        "test-runner": AgentDefinition(
            description="Runs the test suite and analyzes failures.",
            prompt="You run tests and summarize what failed and why.",
            tools=["Bash", "Read", "Grep"],             # Bash so it can execute tests
        ),
    },
)
```

A sound decomposition makes four decisions for every subtask:

- **Boundaries — what is one subtask?** Split along lines that isolate context: a unit of work whose intermediate reading and reasoning the parent doesn't need to see. The `description` field is load-bearing — Claude "determines whether to invoke them based on each subagent's `description`" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)), so each subtask should be describable in one clear sentence.
- **Dependencies — what must finish first?** Independent subtasks form a parallel batch; a subtask that *consumes* others' results (a synthesis, a merge) runs in a later batch. This dependency graph is the core of the plan: the three PR finders depend on nothing and run together; the synthesis depends on all three and runs after.
- **Tools — least privilege.** Grant each subagent only the tools its job requires. A read-only analyzer gets `Read`/`Grep`/`Glob`; a test runner additionally gets `Bash`. Omitting `tools` inherits everything — convenient, but the opposite of least privilege ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).
- **Handoff — what does the subagent need passed in?** A subagent inherits no parent history: "the only channel from parent to subagent is the Agent tool's prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).

### The hard constraint: decomposition is one level

There is a rule that shapes every decomposition: **subagents cannot spawn their own subagents.** The docs are explicit — "Subagents cannot spawn their own subagents. Don't include `Agent` in a subagent's `tools` array" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). The coordinator (your main agent) splits the work; the subagents do leaf-level work and return. You cannot build a tree of delegation by giving a subagent the `Agent` tool and hoping it sub-delegates — it can't. If a "subtask" is itself so big it would need to delegate, that's a sign the *coordinator* should split it further, not that the subagent should.

When a job genuinely needs more than a handful of subagents — "dozens to hundreds of agents" — that's the boundary where turn-by-turn delegation gives way to the **`Workflow` tool / dynamic workflows**, which moves orchestration into a script the runtime executes in an isolated environment, separate from your conversation ([Agent SDK dynamic workflows](https://code.claude.com/docs/en/workflows)). How that script-orchestrated model differs from turn-by-turn delegation is its own topic. For the decomposition sizes this lesson covers, plain subagent delegation is the right tool; know the escalation exists.

## Worked example

Decompose "review this PR" into a plan: three independent read-only finders in one parallel batch, then a synthesis that consumes their findings.

```python
READ_ONLY = ["Read", "Grep", "Glob"]
TEST_RUNNER = ["Bash", "Read", "Grep"]


def decompose(task):
    finders = [
        {"name": "style-checker",    "tools": READ_ONLY,   "depends_on": [], "parallel_group": 0},
        {"name": "security-scanner", "tools": READ_ONLY,   "depends_on": [], "parallel_group": 0},
        {"name": "test-runner",      "tools": TEST_RUNNER, "depends_on": [], "parallel_group": 0},
    ]
    synthesis = {
        "name": "synthesis",
        "tools": READ_ONLY,
        "depends_on": [f["name"] for f in finders],   # needs all three results
        "parallel_group": 1,                          # so it runs in a later batch
    }
    return finders + [synthesis]
```

Reading the plan:

- **The three finders share `parallel_group` 0 with `depends_on: []`.** Nothing connects them, so they run concurrently — the parallelization win. Serializing them here would waste wall-clock for no reason.
- **`synthesis` is `parallel_group` 1 and depends on all three.** It reads their outputs, so it *cannot* run until they finish. Placing it in group 0 would be a dependency inversion — asking it to consume results that don't exist yet.
- **Tools are least-privilege.** The finders can't modify or execute; only `test-runner` has `Bash`, because only it needs to run tests. None has `Agent` — the one-level rule.
- **Each name is a job describable in a sentence**, which is what lets the coordinator route work to the right subagent.

The exercise has you build this `decompose`, plus a `validate_plan` that catches the three structural mistakes — `Agent` in a subagent's tools, an unknown dependency, and a dependency inversion — and a `parallel_batches` that groups the names into ordered batches.

## Anti-patterns & pitfalls

1. **The monolith — not decomposing at all.** One agent doing style, security, tests, and synthesis in a single context. It loses context isolation (every file the security pass reads pollutes the conversation), forfeits parallelism, and can't apply least privilege (the one agent needs every tool). When a task has separable parts, the prescribed design is to split it into focused subagents, not to scale up one agent.

2. **Giving a subagent the `Agent` tool / expecting nested delegation.** Building a delegation tree by letting a subagent spawn its own subagents. The platform forbids it — "Don't include `Agent` in a subagent's `tools` array" ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Decomposition is one level; if a subtask is too big, the coordinator splits it further.

3. **Getting the dependency graph wrong.** Two failure modes, both real: running dependent subtasks in parallel (a synthesis can't start before the finders it consumes finish — a dependency inversion), or serializing genuinely independent ones (running the three finders one after another throws away the parallelization win). Map what truly depends on what, then parallelize the rest.

4. **Over-broad tool grants.** Handing a read-only analyzer `Write` or `Bash` "just in case." It widens the blast radius for no benefit; scope each subagent to exactly its job ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).

5. **Assuming inherited context.** Expecting a subagent to "already know" a file path or a prior decision. It receives only its prompt string and its own system prompt — no parent history ([Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)). Pass what it needs explicitly.

## Exam focus

Decomposition underlies every multi-agent scenario:

- **Multi-Agent Research System** — a coordinator splitting research across parallel investigators, then synthesizing. The canonical decomposition question, and the canonical "subagents can't spawn subagents" trap.
- **Code Generation / Developer Productivity** — parallel review passes plus a synthesis, with least-privilege tool sets per pass.

The reliable distractors: a nested-delegation design (a subagent that spawns subagents — impossible), a single mega-agent (no decomposition), a plan that parallelizes a dependent step or serializes independent ones, or an analyzer over-granted write/exec tools. The correct answer decomposes into focused, least-privilege subagents with a correct dependency order — one level deep.

## References & further reading

- [Agent SDK — Subagents in the SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — `AgentDefinition`, the three benefits (context isolation, parallelization, tool restriction), the prompt-string handoff boundary, and the rule that subagents cannot spawn subagents.
- [Agent SDK — Dynamic workflows](https://code.claude.com/docs/en/workflows) — where decomposition scales past a handful of subagents into a script-orchestrated run, and how that differs from turn-by-turn delegation.

## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.6: Design task decomposition strategies for complex workflows.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
