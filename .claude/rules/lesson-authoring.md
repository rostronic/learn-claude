---
paths: ["lessons/**/*.md"]
---

# Lesson authoring rules

These rules load whenever you edit any markdown file under `lessons/`. They build on the editorial constitution in the root [CLAUDE.md](../../CLAUDE.md) — read that first if you haven't.

## Required frontmatter

Every `lesson.md` opens with a YAML frontmatter block. It's machine-readable on purpose: tooling surfaces it in the curriculum map, lints the links, and lets us upgrade lessons in place.

```yaml
---
lesson_id: "1.1"
task_statement: "1.1 Design and implement agentic loops for autonomous task execution"
exam_guide_reference: "Domain 1, Task Statement 1.1"
references:
  - title: "Agent SDK — How the agent loop works"
    url: "https://code.claude.com/docs/en/agent-sdk/agent-loop"
    type: official_docs        # official_docs | exam_guide
    covers: "Loop lifecycle, turns, stop_reason, tool execution"
  - title: "CCA-F Exam Guide — Domain 1, Task Statement 1.1"
    url: "https://everpath-course-content.s3-accelerate.amazonaws.com/…/Claude+Certified+Architect+–+Foundations+Certification+Exam+Guide.pdf"
    type: exam_guide
    covers: "Scope authority; the three loop anti-patterns"
---
```

Field rules:
- **`lesson_id`, `task_statement`, `exam_guide_reference`** — the same identifiers used in `rubric.yaml`. `task_statement` is verbatim from the exam guide (ID + full title).
- **`references`** — a list. **At least one `type: official_docs` entry and exactly one `type: exam_guide` entry are required.** Every `official_docs` `url` must be on an official Anthropic/Claude domain (`docs.claude.com`, `code.claude.com`, `platform.claude.com`). No third-party domains. `covers` is a short note on what that source backs in the lesson.

## Required opening line

Immediately after the frontmatter, the first heading is the **exact task statement ID and title from the CCA-F exam guide**, copy-pasted verbatim. No paraphrasing. No "this lesson covers…" preamble.

```markdown
# Task Statement 1.1: Design and implement agentic loops for autonomous task execution
```

Same rule for `exercise.md` — open with the task statement ID and title so a reader landing directly on the exercise knows what they're being graded against.

## Required structure (lessons)

`lesson.md` follows this six-section structure, in this order. Each section teaches the topic positively first; the anti-patterns are one section, not the spine.

1. **Overview** — what this is, where it fits in the broader Claude toolkit, and why it matters. A brief orientation (a few short paragraphs) is welcome here. State the task statement plainly.
2. **How it works** — the mechanism, taught in depth. This is the core of the lesson. Explain the model/SDK behavior accurately, with **inline citations** to the `references:` docs where you make a claim (e.g. "the loop ends when Claude returns no tool calls ([agent loop docs](…))"). Include runnable `anthropic`-SDK code that illustrates the mechanism.
3. **Worked example** — a complete, runnable example that puts the mechanism to work end-to-end. Real code, not pseudocode. Walk the reader through it.
4. **Anti-patterns & pitfalls** — the wrong approaches the exam tempts you with, and *why* each fails. Quote the exam guide's language when it lists anti-patterns (Task Statement 1.1 names three, for example). Be definitive; the "Anthropic way" rule applies.
5. **Exam focus** — short. Which CCA-F scenarios (1–6) this task statement powers, and what distractors the exam reliably offers. This is the in-lesson hook; the dedicated exam-prep + practice-exam experience is a separate, future feature (Phase 3).
6. **References & further reading** — render the frontmatter `references:` as a readable list (title + link + what it covers), plus any prose pointers to adjacent official docs.

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
