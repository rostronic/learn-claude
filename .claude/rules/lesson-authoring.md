---
paths: ["lessons/**/*.md"]
---

# Lesson authoring rules

These rules load whenever you edit any markdown file under `lessons/`. They build on the editorial constitution in the root [CLAUDE.md](../../CLAUDE.md) — read that first if you haven't.

## Required frontmatter

Every `lesson.md` opens with a YAML frontmatter block. It's machine-readable on purpose: tooling surfaces it in the curriculum map, lints the links, and lets us upgrade lessons in place.

```yaml
---
chapter: "3.1"                 # course id = module.lesson — the learning-order address
slug: "agentic-loops"
title: "Agentic loops"
module: "module-3-agentic-core"
sequence: 8                    # global position in the learning path (drives "next lesson")
references:
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs
    covers: "Loop lifecycle, turns, stop_reason, tool execution"
---
```

Field rules:
- **`chapter`** — `module.lesson`, the course-order address (e.g. `3.1`). Matches the directory `<chapter>-<slug>/` and the `chapter` in `rubric.yaml`. It is **course order, never an exam ID**, and is renumbered freely when the learning path changes.
- **`slug` / `title` / `module` / `sequence`** — `slug` matches the directory; `title` is the lesson's H1; `module` is the containing folder; `sequence` is the lesson's global position in the learning path (drives "next lesson").
- **`references`** — a list of **official docs only**. **At least one entry**, and every `url` must be on an official Anthropic/Claude domain (`docs.claude.com`, `code.claude.com`, `platform.claude.com`). No third-party domains, and **no exam-guide entries here** — exam alignment lives in `docs/exam-mapping.md` and the lesson's "Exam coverage" footer, not in `references`.

## Required opening line

Immediately after the frontmatter, the first heading is the lesson **title** (the `title` field) as a plain `#` H1 — the topic, not an exam's task statement. No "Task Statement …" prefix, no "this lesson covers…" preamble.

```markdown
# Agentic loops
```

`exercise.md` opens with `# <title> — exercise`.

## Exam coverage footer

Lessons are exam-agnostic, but if a lesson covers one or more exams, end it with an informational **"## Exam coverage"** footer: one bullet per exam giving the exam code, domain, and task statement, then a pointer to `docs/exam-mapping.md`. This is for the reader — the **authoritative** record is `docs/exam-mapping.md`, and the two must agree. Omit the section entirely for unmapped ("just learn Claude") lessons.

```markdown
## Exam coverage

- **CCAF** — Domain 1 (Agentic Architecture & Orchestration), Task Statement 1.1: Design and implement agentic loops for autonomous task execution.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
```

## Required structure (lessons)

`lesson.md` follows this structure, in this order. Each section teaches the topic positively first; the anti-patterns are one section, not the spine.

1. **Overview** — what this is, where it fits in the broader Claude toolkit, and why it matters. A brief orientation (a few short paragraphs) is welcome here. State the task statement plainly.
2. **How it works** — the mechanism, taught in depth. This is the core of the lesson. Explain the model/SDK behavior accurately, with **inline citations** to the `references:` docs where you make a claim (e.g. "the loop ends when Claude returns no tool calls ([agent loop docs](…))"). Include runnable `anthropic`-SDK code that illustrates the mechanism.
3. **Worked example** — a complete, runnable example that puts the mechanism to work end-to-end. Real code, not pseudocode. Walk the reader through it.
4. **Anti-patterns & pitfalls** — the wrong approaches the exam tempts you with, and *why* each fails. Quote the exam guide's language when it lists anti-patterns (Task Statement 1.1 names three, for example). Be definitive; the "Anthropic way" rule applies.
5. **Exam focus** *(optional — include only if the lesson maps to an exam)* — short: which of that exam's scenarios/areas this topic powers and what distractors it reliably offers. The dedicated exam-prep + practice-exam experience is a separate, future feature.
6. **References & further reading** — render the frontmatter `references:` as a readable list (title + link + what it covers), plus any prose pointers to adjacent official docs.
7. **Exam coverage** *(footer — required when the lesson maps to an exam, omitted otherwise)* — the informational mapping described under "Exam coverage footer" above.

## Length & reading time

No hard word cap. Instead, target each **section** as a **5–10 minute read** — long enough to teach properly, short enough to stay focused. If a section runs much past ~10 minutes, split the idea or move detail into the exercise. Depth is good; padding is not. Every paragraph should either teach the mechanism, show code, or name an exam trap.

## Code requirements

- All code examples are **runnable Python** using the `anthropic` SDK (`pip install anthropic`).
- Show real API shapes: `client.messages.create(...)`, `response.stop_reason`, `content[0].input`, etc. Don't invent method names.
- Use `claude-sonnet-4-6` or `claude-opus-4-8` as the model in examples — the latest stable IDs as of this repo's writing. Don't reference retired models.
- If you show a tool schema, show the real Claude tool-use schema shape: `{"name": ..., "description": ..., "input_schema": {...}}`.

## What not to do

- **Don't summarize the exam guide.** Cite it for scope and teach the topic from the official docs. Summarizing is what students do; we're teaching students.
- **Don't add background on LLMs, transformers, or "what is an agent."** Audience is working engineers — they know.
- **Don't equivocate.** If the exam has a correct answer, state it. "There are tradeoffs" is the wrong register for this material.
- **Don't cite third-party blogs, videos, or tutorials.** Teaching references must be official Anthropic/Claude docs (`docs.claude.com`, `code.claude.com`, `platform.claude.com`) and must appear in the lesson's `references:` frontmatter. Everything else dilutes the source of truth.
