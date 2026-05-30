# Curriculum map

Learn Claude is organized as a **learning path**: a dependency-ordered sequence where each chapter builds on the ones before it. Chapters are numbered `module.lesson` purely by **course order** — the numbers are the learning sequence, not an exam's numbering. Address a chapter by its number (e.g. `/study 3.1`).

Lessons are **exam-agnostic**. Which chapter covers which exam's task statements (and in what exam order) lives in **[`exam-mapping.md`](exam-mapping.md)** — the single source of truth for exam coverage — and is restated in each lesson's "Exam coverage" footer. Today the only exam mapped is **CCAF** (Claude Certified Architect — Foundations).

To study the path **in an exam's order** instead of course order, run `/exam <CODE>` (e.g. `/exam CCAF`): it reads the mapping, lists that exam's task statements in exam order, and walks you through the built chapters one at a time.

**Status:** 37 of 37 chapters built (0.1, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10). The rest are planned.

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
| 4.1 | Multi-step workflows with enforcement & handoff | **built** |
| 4.2 | Agent SDK hooks for tool interception & normalization | **built** |
| 4.3 | Task decomposition strategies | **built** |
| 4.4 | Session state, resumption, and forking | **built** |

## Module 5 — Claude Code & MCP integration

| Chapter | Title | Status |
|---|---|---|
| 5.1 | CLAUDE.md hierarchy, scoping & modular organization | **built** |
| 5.2 | Path-specific rules for conditional conventions | **built** |
| 5.3 | Custom slash commands and skills | **built** |
| 5.4 | Plan mode vs direct execution | **built** |
| 5.5 | Integrating MCP servers | **built** |
| 5.6 | Iterative refinement techniques | **built** |
| 5.7 | Claude Code in CI/CD pipelines | **built** |
| 5.8 | Capstone — Developer Productivity with Claude | **built** |

## Module 6 — Extraction & quality loops

| Chapter | Title | Status |
|---|---|---|
| 6.1 | Validation, retry & feedback loops for extraction | **built** |
| 6.2 | Batch processing strategies | **built** |
| 6.3 | Multi-instance & multi-pass review architectures | **built** |
| 6.4 | Capstone — Claude Code for Continuous Integration | **built** |

## Module 7 — Context & reliability

| Chapter | Title | Status |
|---|---|---|
| 7.1 | Managing conversation context across long interactions | **built** |
| 7.2 | Context in large codebase exploration | **built** |
| 7.3 | Escalation & ambiguity resolution | **built** |
| 7.4 | Error propagation across multi-agent systems | **built** |
| 7.5 | Human review workflows & confidence calibration | **built** |
| 7.6 | Information provenance & uncertainty in synthesis | **built** |
| 7.7 | Capstone — Customer Support Resolution Agent | **built** |
| 7.8 | Capstone — Multi-Agent Research System | **built** |
| 7.9 | Capstone — Code Generation with Claude Code | **built** |
| 7.10 | Capstone — Structured Data Extraction | **built** |

---

**Totals:** 37 chapters across 8 modules. The 6 capstones (5.8, 6.4, 7.7–7.10) are the CCAF exam scenarios, placed after their prerequisite material. For the exam-order view of all this, see [`exam-mapping.md`](exam-mapping.md).
