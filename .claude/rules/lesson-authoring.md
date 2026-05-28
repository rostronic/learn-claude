---
paths: ["lessons/**/*.md"]
---

# Lesson authoring rules

These rules load whenever you edit any markdown file under `lessons/`. They build on the editorial constitution in the root [CLAUDE.md](../../CLAUDE.md) — read that first if you haven't.

## Required opening line

Every `lesson.md` starts with the **exact task statement ID and title from the CCA-F exam guide**, copy-pasted verbatim. No paraphrasing. No "this lesson covers…" preamble.

```markdown
# Task Statement 1.1: Design and implement agentic loops for autonomous task execution
```

Same rule for `exercise.md` — open with the task statement ID and title so a reader landing directly on the exercise knows what they're being graded against.

## Required structure (lessons)

`lesson.md` follows this five-section structure, in this order:

1. **Concept** — what the thing is, in 2–3 paragraphs. Mechanism, not motivation.
2. **Anti-pattern** — the wrong approach the exam will tempt you with. Quote the exam guide's language for the anti-pattern when it gives one (Task Statement 1.1 lists three specific ones, for example). Explain *why* it fails.
3. **Correct pattern** — the Anthropic-prescribed approach. Be definitive; "Anthropic way" rule from the constitution applies.
4. **Worked example** — runnable Python that demonstrates the correct pattern. Uses the `anthropic` SDK. Short enough to read on a screen without scrolling. Real code, not pseudocode.
5. **Why this matters on the exam** — name the scenarios (1–6 from the exam guide) where this task statement shows up. Be specific: "this is the foundation for every question about agent reliability in Scenarios 1, 3, and 4" beats "this is important."

## Length cap

Hard cap: **~800 words.** If you're over, you're explaining too much. Move depth into the exercise — the reader learns by building, not by reading. The exam tests judgment under scenario pressure; long prose lessons don't build that muscle.

## Code requirements

- All code examples are **runnable Python** using the `anthropic` SDK (`pip install anthropic`).
- Show real API shapes: `client.messages.create(...)`, `response.stop_reason`, `content[0].input`, etc. Don't invent method names.
- Use `claude-sonnet-4-6` or `claude-opus-4-7` as the model in examples — the latest stable IDs as of this repo's writing. Don't reference retired models.
- If you show a tool schema, show the real Claude tool-use schema shape: `{"name": ..., "description": ..., "input_schema": {...}}`.

## What not to do

- **Don't summarize the exam guide.** Cite it and teach what it teaches. Summarizing is what students do; we're teaching students.
- **Don't add background on LLMs, transformers, or "what is an agent."** Audience is working engineers — they know.
- **Don't equivocate.** If the exam has a correct answer, state it. "There are tradeoffs" is the wrong register for this material.
- **Don't link out to external blogs or videos.** The exam guide is the source of truth; everything else dilutes it.
