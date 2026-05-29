---
# Single source of truth for exam → lesson mappings across the whole project.
# Lessons are exam-agnostic; this file (and each lesson's "Exam coverage" footer) records
# which course chapter covers each exam's task statements, in that exam's own order.
# The `/exam <CODE>` command reads this to present a chosen exam's lessons in exam order.
exams:
  CCAF:
    title: "Claude Certified Architect — Foundations"
    guide_url: "https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F8lsy243ftffjjy1cx9lm3o2bw%2Fpublic%2F1773274827%2FClaude+Certified+Architect+%E2%80%93+Foundations+Certification+Exam+Guide.pdf"
    coverage:                       # in CCAF's own order (Domain 1 → 5, then scenarios)
      - { task_statement: "1.1 Design and implement agentic loops for autonomous task execution", domain: 1, lesson_chapter: "3.1", lesson_slug: "agentic-loops", status: built }
      - { task_statement: "1.2 Orchestrate multi-agent systems with coordinator-subagent patterns", domain: 1, lesson_chapter: "3.2", lesson_slug: "coordinator-subagent", status: built }
      - { task_statement: "1.3 Configure subagent invocation, context passing, and spawning", domain: 1, lesson_chapter: "3.3", lesson_slug: "subagent-invocation", status: built }
      - { task_statement: "1.4 Implement multi-step workflows with enforcement and handoff patterns", domain: 1, lesson_chapter: "4.1", status: planned }
      - { task_statement: "1.5 Apply Agent SDK hooks for tool call interception and data normalization", domain: 1, lesson_chapter: "4.2", status: planned }
      - { task_statement: "1.6 Design task decomposition strategies for complex workflows", domain: 1, lesson_chapter: "4.3", status: planned }
      - { task_statement: "1.7 Manage session state, resumption, and forking", domain: 1, lesson_chapter: "4.4", status: planned }
      - { task_statement: "2.1 Design effective tool interfaces with clear descriptions and boundaries", domain: 2, lesson_chapter: "2.2", status: planned }
      - { task_statement: "2.2 Implement structured error responses for MCP tools", domain: 2, lesson_chapter: "2.3", status: planned }
      - { task_statement: "2.3 Distribute tools appropriately across agents and configure tool choice", domain: 2, lesson_chapter: "3.4", lesson_slug: "tool-distribution", status: built }
      - { task_statement: "2.4 Integrate MCP servers into Claude Code and agent workflows", domain: 2, lesson_chapter: "5.5", status: planned }
      - { task_statement: "2.5 Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively", domain: 2, lesson_chapter: "2.1", status: planned }
      - { task_statement: "3.1 Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization", domain: 3, lesson_chapter: "5.1", status: planned }
      - { task_statement: "3.2 Create and configure custom slash commands and skills", domain: 3, lesson_chapter: "5.3", status: planned }
      - { task_statement: "3.3 Apply path-specific rules for conditional convention loading", domain: 3, lesson_chapter: "5.2", status: planned }
      - { task_statement: "3.4 Determine when to use plan mode vs direct execution", domain: 3, lesson_chapter: "5.4", status: planned }
      - { task_statement: "3.5 Apply iterative refinement techniques for progressive improvement", domain: 3, lesson_chapter: "5.6", status: planned }
      - { task_statement: "3.6 Integrate Claude Code into CI/CD pipelines", domain: 3, lesson_chapter: "5.7", status: planned }
      - { task_statement: "4.1 Design prompts with explicit criteria to improve precision and reduce false positives", domain: 4, lesson_chapter: "1.1", lesson_slug: "explicit-criteria", status: built }
      - { task_statement: "4.2 Apply few-shot prompting to improve output consistency and quality", domain: 4, lesson_chapter: "1.2", lesson_slug: "few-shot", status: built }
      - { task_statement: "4.3 Enforce structured output using tool use and JSON schemas", domain: 4, lesson_chapter: "1.3", lesson_slug: "structured-output", status: built }
      - { task_statement: "4.4 Implement validation, retry, and feedback loops for extraction quality", domain: 4, lesson_chapter: "6.1", status: planned }
      - { task_statement: "4.5 Design efficient batch processing strategies", domain: 4, lesson_chapter: "6.2", status: planned }
      - { task_statement: "4.6 Design multi-instance and multi-pass review architectures", domain: 4, lesson_chapter: "6.3", status: planned }
      - { task_statement: "5.1 Manage conversation context to preserve critical information across long interactions", domain: 5, lesson_chapter: "7.1", status: planned }
      - { task_statement: "5.2 Design effective escalation and ambiguity resolution patterns", domain: 5, lesson_chapter: "7.3", status: planned }
      - { task_statement: "5.3 Implement error propagation strategies across multi-agent systems", domain: 5, lesson_chapter: "7.4", status: planned }
      - { task_statement: "5.4 Manage context effectively in large codebase exploration", domain: 5, lesson_chapter: "7.2", status: planned }
      - { task_statement: "5.5 Design human review workflows and confidence calibration", domain: 5, lesson_chapter: "7.5", status: planned }
      - { task_statement: "5.6 Preserve information provenance and handle uncertainty in multi-source synthesis", domain: 5, lesson_chapter: "7.6", status: planned }
      - { task_statement: "Scenario 1: Customer Support Resolution Agent", domain: "scenario", lesson_chapter: "7.7", status: planned }
      - { task_statement: "Scenario 2: Code Generation with Claude Code", domain: "scenario", lesson_chapter: "7.9", status: planned }
      - { task_statement: "Scenario 3: Multi-Agent Research System", domain: "scenario", lesson_chapter: "7.8", status: planned }
      - { task_statement: "Scenario 4: Developer Productivity with Claude", domain: "scenario", lesson_chapter: "5.8", status: planned }
      - { task_statement: "Scenario 5: Claude Code for Continuous Integration", domain: "scenario", lesson_chapter: "6.4", status: planned }
      - { task_statement: "Scenario 6: Structured Data Extraction", domain: "scenario", lesson_chapter: "7.10", status: planned }
---

# Exam mapping

**This file is the single source of truth for exam → lesson mappings across Learn Claude.** Lessons themselves are exam-agnostic (organized by the learning path in [`curriculum-map.md`](curriculum-map.md)); this file records which course **chapter** covers each exam's task statements, in that exam's own order. Each lesson also restates its mapping in an informational "Exam coverage" footer. The `/exam <CODE>` command (e.g. `/exam CCAF`) reads the `exams:` frontmatter here to present a chosen exam's chapters in exam order and walk you through the built ones.

Adding another exam later = adding a key under `exams:` and listing its coverage. Lessons need not change.

## CCAF — Claude Certified Architect (Foundations)

The course was reordered into a dependency-driven learning path, so CCAF's task statements are spread across the modules below. This table is in **CCAF's own order**; the **Chapter** column is where to learn that material in the course. (Seven chapters are built so far — 1.1–1.3 and 3.1–3.4; the rest are planned — see the curriculum map.)

| CCAF | Task statement | Domain | Course chapter | Status |
|---|---|---|---|---|
| 1.1 | Design and implement agentic loops for autonomous task execution | 1 | 3.1 | built |
| 1.2 | Orchestrate multi-agent systems with coordinator-subagent patterns | 1 | 3.2 | built |
| 1.3 | Configure subagent invocation, context passing, and spawning | 1 | 3.3 | built |
| 1.4 | Implement multi-step workflows with enforcement and handoff patterns | 1 | 4.1 | planned |
| 1.5 | Apply Agent SDK hooks for tool call interception and data normalization | 1 | 4.2 | planned |
| 1.6 | Design task decomposition strategies for complex workflows | 1 | 4.3 | planned |
| 1.7 | Manage session state, resumption, and forking | 1 | 4.4 | planned |
| 2.1 | Design effective tool interfaces with clear descriptions and boundaries | 2 | 2.2 | planned |
| 2.2 | Implement structured error responses for MCP tools | 2 | 2.3 | planned |
| 2.3 | Distribute tools appropriately across agents and configure tool choice | 2 | 3.4 | built |
| 2.4 | Integrate MCP servers into Claude Code and agent workflows | 2 | 5.5 | planned |
| 2.5 | Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively | 2 | 2.1 | planned |
| 3.1 | Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization | 3 | 5.1 | planned |
| 3.2 | Create and configure custom slash commands and skills | 3 | 5.3 | planned |
| 3.3 | Apply path-specific rules for conditional convention loading | 3 | 5.2 | planned |
| 3.4 | Determine when to use plan mode vs direct execution | 3 | 5.4 | planned |
| 3.5 | Apply iterative refinement techniques for progressive improvement | 3 | 5.6 | planned |
| 3.6 | Integrate Claude Code into CI/CD pipelines | 3 | 5.7 | planned |
| 4.1 | Design prompts with explicit criteria to improve precision and reduce false positives | 4 | 1.1 | built |
| 4.2 | Apply few-shot prompting to improve output consistency and quality | 4 | 1.2 | built |
| 4.3 | Enforce structured output using tool use and JSON schemas | 4 | 1.3 | built |
| 4.4 | Implement validation, retry, and feedback loops for extraction quality | 4 | 6.1 | planned |
| 4.5 | Design efficient batch processing strategies | 4 | 6.2 | planned |
| 4.6 | Design multi-instance and multi-pass review architectures | 4 | 6.3 | planned |
| 5.1 | Manage conversation context to preserve critical information across long interactions | 5 | 7.1 | planned |
| 5.2 | Design effective escalation and ambiguity resolution patterns | 5 | 7.3 | planned |
| 5.3 | Implement error propagation strategies across multi-agent systems | 5 | 7.4 | planned |
| 5.4 | Manage context effectively in large codebase exploration | 5 | 7.2 | planned |
| 5.5 | Design human review workflows and confidence calibration | 5 | 7.5 | planned |
| 5.6 | Preserve information provenance and handle uncertainty in multi-source synthesis | 5 | 7.6 | planned |
| Scenario 1 | Customer Support Resolution Agent | scenario | 7.7 | planned |
| Scenario 2 | Code Generation with Claude Code | scenario | 7.9 | planned |
| Scenario 3 | Multi-Agent Research System | scenario | 7.8 | planned |
| Scenario 4 | Developer Productivity with Claude | scenario | 5.8 | planned |
| Scenario 5 | Claude Code for Continuous Integration | scenario | 6.4 | planned |
| Scenario 6 | Structured Data Extraction | scenario | 7.10 | planned |

**Coverage:** all 30 CCAF task statements + 6 scenarios are mapped to exactly one course chapter. 7 of 36 are built (1.1–1.3, 3.1–3.4).
