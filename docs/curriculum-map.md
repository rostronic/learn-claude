# Curriculum map

Learn Claude is organized as a **learning path**: a dependency-ordered sequence where each chapter builds on the ones before it. Chapters are numbered `module.lesson` purely by **course order** — the numbers are the learning sequence, not an exam's numbering. Address a chapter by its number (e.g. `/study 3.1`).

Lessons are **exam-agnostic**. Which chapter covers which exam's task statements (and in what exam order) lives in **[`exam-mapping.md`](exam-mapping.md)** — the single source of truth for exam coverage — and is restated in each lesson's "Exam coverage" footer. Today the only exam mapped is **CCAF** (Claude Certified Architect — Foundations).

To study the path **in an exam's order** instead of course order, run `/exam <CODE>` (e.g. `/exam CCAF`): it reads the mapping, lists that exam's task statements in exam order, and walks you through the built chapters one at a time.

**Status:** 11 of 37 chapters built (0.1, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4). The rest are planned.

## Module 0 — Foundations

| Chapter | Title | Status |
|---|---|---|
| 0.1 | Foundations: the four technologies (Claude API, Agent SDK, Claude Code, MCP) | **built** |

## Module 1 — Prompting & structured output

| Chapter | Title | Status |
|---|---|---|
| 1.1 | Prompting with explicit criteria | **built** |
| 1.2 | Few-shot prompting | **built** |
| 1.3 | Structured output with tool use & JSON schemas | **built** |

## Module 2 — Tools

| Chapter | Title | Status |
|---|---|---|
| 2.1 | Built-in tools (Read, Write, Edit, Bash, Grep, Glob) | **built** |
| 2.2 | Designing tool interfaces | **built** |
| 2.3 | Structured error responses for tools | **built** |

## Module 3 — Agentic core

| Chapter | Title | Status |
|---|---|---|
| 3.1 | Agentic loops | **built** |
| 3.2 | Coordinator and subagent orchestration | **built** |
| 3.3 | Subagent invocation and context passing | **built** |
| 3.4 | Distributing tools across agents & tool choice | **built** |

## Module 4 — Workflows & state

| Chapter | Title | Status |
|---|---|---|
| 4.1 | Multi-step workflows with enforcement & handoff | planned |
| 4.2 | Agent SDK hooks for tool interception & normalization | planned |
| 4.3 | Task decomposition strategies | planned |
| 4.4 | Session state, resumption, and forking | planned |

## Module 5 — Claude Code & MCP integration

| Chapter | Title | Status |
|---|---|---|
| 5.1 | CLAUDE.md hierarchy, scoping & modular organization | planned |
| 5.2 | Path-specific rules for conditional conventions | planned |
| 5.3 | Custom slash commands and skills | planned |
| 5.4 | Plan mode vs direct execution | planned |
| 5.5 | Integrating MCP servers | planned |
| 5.6 | Iterative refinement techniques | planned |
| 5.7 | Claude Code in CI/CD pipelines | planned |
| 5.8 | Capstone — Developer Productivity with Claude | planned |

## Module 6 — Extraction & quality loops

| Chapter | Title | Status |
|---|---|---|
| 6.1 | Validation, retry & feedback loops for extraction | planned |
| 6.2 | Batch processing strategies | planned |
| 6.3 | Multi-instance & multi-pass review architectures | planned |
| 6.4 | Capstone — Claude Code for Continuous Integration | planned |

## Module 7 — Context & reliability

| Chapter | Title | Status |
|---|---|---|
| 7.1 | Managing conversation context across long interactions | planned |
| 7.2 | Context in large codebase exploration | planned |
| 7.3 | Escalation & ambiguity resolution | planned |
| 7.4 | Error propagation across multi-agent systems | planned |
| 7.5 | Human review workflows & confidence calibration | planned |
| 7.6 | Information provenance & uncertainty in synthesis | planned |
| 7.7 | Capstone — Customer Support Resolution Agent | planned |
| 7.8 | Capstone — Multi-Agent Research System | planned |
| 7.9 | Capstone — Code Generation with Claude Code | planned |
| 7.10 | Capstone — Structured Data Extraction | planned |

---

**Totals:** 37 chapters across 8 modules. The 4 capstones (5.8, 6.4, 7.7–7.10) are the CCAF exam scenarios, placed after their prerequisite material. For the exam-order view of all this, see [`exam-mapping.md`](exam-mapping.md).
