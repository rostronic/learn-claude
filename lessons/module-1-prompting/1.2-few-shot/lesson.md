---
chapter: "1.2"
slug: "few-shot"
title: "Few-shot prompting"
module: "module-1-prompting"
sequence: 3
references:
  - title: "Prompting best practices — Use examples effectively"
    url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices"
    type: official_docs
    covers: "Few-shot / multishot prompting; relevant, diverse, structured examples; <example> tags; how many"
  - title: "Prompt engineering overview"
    url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview"
    type: official_docs
    covers: "Where examples fit among prompting techniques"
---

# Few-shot prompting

## Overview

Chapter 1.1 made your criteria explicit. But some judgments are hard to fully specify in prose — "is this comment a genuine bug or an acceptable local pattern?" is easier to *show* than to define. That's what few-shot (a.k.a. multishot) prompting is for: you hand Claude a handful of worked examples, and it generalizes the judgment to new cases. The docs are blunt about how effective this is — "Examples are one of the most reliable ways to steer Claude's output format, tone, and structure. A few well-crafted examples… can dramatically improve accuracy and consistency" ([Use examples effectively](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)).

Reach for few-shot when "detailed instructions alone produce inconsistent results" (CCAF Domain 4) — inconsistent formatting, wobbly handling of ambiguous cases, or hallucinated fields in extraction. Examples pin all three down.

## How it works

A few-shot prompt is your instruction plus a set of input→output examples, each clearly delimited so the model can tell examples from instructions. The official guidance: make your examples **relevant** (mirror the real use case), **diverse** (cover edge cases and vary enough that Claude doesn't latch onto an unintended pattern), and **structured** ("Wrap examples in `<example>` tags (multiple examples in `<examples>` tags) so Claude can distinguish them from instructions") ([best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)).

Three properties make examples actually work, and the exam emphasizes each:

1. **They show *judgment*, not just format.** For ambiguous scenarios, an example should "show reasoning for why one action was chosen over plausible alternatives" (CCAF 4.2). An example that just maps input→label teaches pattern-matching; an example that explains *why* teaches the boundary.
2. **They're diverse — especially across classes.** Examples that all point one way teach the model to always answer that way. To reduce false positives you must include examples "distinguishing acceptable code patterns from genuine issues" (CCAF 4.2): both the thing to flag *and* the look-alike thing to leave alone. Diversity is what enables generalization "to novel patterns rather than matching only pre-specified cases."
3. **They demonstrate the exact output shape.** If you want `location, issue, severity, suggested fix`, an example that produces exactly that structure is more reliable than describing it.

How many? A few. The exam's guidance for targeted, ambiguous cases is "2–4 targeted few-shot examples"; the general docs suggest "3–5 examples for best results." Either way the point is *a small, carefully chosen, diverse set* — not one, and not fifty.

## Worked example

A builder that assembles a structured few-shot prompt and enforces the two properties that matter most: enough examples, and more than one class represented.

```python
def build_few_shot_prompt(instruction, examples):
    """examples: list of {"input": str, "output": str, "label": str (optional)}."""
    if len(examples) < 2:
        raise ValueError("few-shot needs at least 2 examples")
    labels = {e["label"] for e in examples if "label" in e}
    if labels and len(labels) == 1:
        raise ValueError("examples are single-class; include diverse/contrasting cases")

    blocks = []
    for e in examples:
        blocks.append(
            f"<example>\n<input>{e['input']}</input>\n"
            f"<output>{e['output']}</output>\n</example>"
        )
    examples_block = "<examples>\n" + "\n".join(blocks) + "\n</examples>"
    return f"{instruction}\n\n{examples_block}"

prompt = build_few_shot_prompt(
    "Classify each code comment as BUG (contradicts the code) or OK.",
    [
        {"input": "# returns the user's age\ndef get_name(u): return u.name",
         "output": "BUG — comment says age, function returns name", "label": "BUG"},
        {"input": "# fast path for the common case\nif cached: return cached",
         "output": "OK — comment accurately describes the code", "label": "OK"},
    ],
)
```

The examples are wrapped so Claude can't confuse them with the instruction, and they contrast a genuine bug with an acceptable comment — the model learns the *boundary*, not "always say BUG."

## Anti-patterns & pitfalls

1. **Single-class examples.** Every example showing the same label (all BUGs, all positives) teaches the model to always answer that way and inflates false positives. Always include contrasting cases — the issue *and* the acceptable look-alike (CCAF 4.2).
2. **Examples that show format but not reasoning.** For ambiguous decisions, an input→label pair without the *why* teaches surface matching. Show the reasoning for choosing one action over plausible alternatives.
3. **Unstructured examples.** Pasting examples inline without delimiters lets the model blur them with your instructions. Wrap them in `<example>` / `<examples>` tags.
4. **Too few or too many.** One example is an anecdote, not a pattern; dozens bloat context and over-fit. Use a small targeted set (≈2–4 for ambiguous cases, 3–5 generally).

Note the relationship to chapter 1.1: few-shot **complements** explicit criteria, it doesn't replace them. State the criteria, then show examples for the cases prose can't fully pin down.

## Exam focus

Few-shot is the workhorse across **CCAF Scenario 6 (Structured Data Extraction)** — examples covering varied document formats reduce empty/null extraction and hallucinated fields — and the review scenarios (2, 5), where contrasting examples cut false positives. A classic distractor pairs "the output is inconsistent" with "add more detailed instructions"; the exam's answer is few-shot examples (Domain 4: examples beat instructions-alone when results are inconsistent).

## References & further reading

- [Prompting best practices — Use examples effectively](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — few-shot/multishot; relevant + diverse + structured examples; `<example>` tags; how many to include.
- [Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) — where examples sit among the techniques.

## Exam coverage

- **CCAF** — Domain 4 (Prompt Engineering & Structured Output), Task Statement 4.2: Apply few-shot prompting to improve output consistency and quality.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
