---
chapter: "1.1"
slug: "explicit-criteria"
title: "Prompting with explicit criteria"
module: "module-1-prompting"
sequence: 2
references:
  - title: "Prompt engineering overview"
    url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview"
    type: official_docs
    covers: "Define success criteria before prompting; what prompt engineering can and can't fix"
  - title: "Prompting best practices — Be clear and direct"
    url: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices"
    type: official_docs
    covers: "Clear, explicit, specific instructions; provide context/motivation; sequential criteria"
---

# Prompting with explicit criteria

## Overview

The fastest way to make Claude more *precise* — to cut false positives — is almost never "tell it to try harder." It's to replace vague instructions with **explicit, categorical criteria**: a concrete definition of what counts and what doesn't. This is the foundation of the whole prompting module, because every later technique (few-shot, structured output, review architectures) assumes you can already state, unambiguously, what a good answer is.

The official guidance starts here too: before you prompt-engineer at all, you should have "a clear definition of the success criteria for your use case" ([Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)). A prompt is just that definition, written down for the model. If *you* can't state the criteria crisply, the model can't apply them consistently.

## How it works

Claude "responds well to clear, explicit instructions. Being specific about your desired output can help enhance results" ([Be clear and direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)). The doc's golden rule is the test to apply to every prompt: *"Show your prompt to a colleague with minimal context… If they'd be confused, Claude will be too."*

For a precision-sensitive task — say, a code-review agent flagging issues — the difference between a vague and an explicit criterion is the difference between a tool developers trust and one they mute. Compare:

- **Vague:** "Check that comments are accurate." / "Be conservative." / "Only report high-confidence findings."
- **Explicit:** "Flag a comment **only when the claimed behavior contradicts the actual code behavior**."

The vague versions push the decision back onto the model's *confidence*, which is exactly the wrong lever. "Be conservative" doesn't define the boundary; it just asks the model to guess where you'd draw it. The explicit version draws the line for it. Three moves make criteria explicit:

1. **State the categories to report and the categories to skip.** Not "find problems" but "report bugs and security issues; skip minor style and local conventions." Naming both sides is what removes the gray zone.
2. **Define severity with concrete examples.** A `critical` vs `minor` label is itself vague until each level has a worked example of code that qualifies. Concrete anchors make classification repeatable.
3. **Give criteria as instructions, not vibes.** "Provide instructions as sequential steps using numbered lists or bullet points when the order or completeness of steps matters" ([best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)). And add the *why* — "Claude is smart enough to generalize from the explanation."

A precision problem is usually a specification problem. If one category produces too many false positives, the fix is a sharper definition of that category (or temporarily disabling it while you sharpen it) — not a global "be more careful."

## Worked example

A prompt builder that bakes in explicit criteria for a review task — categories to report, categories to skip, and severity anchored to examples:

```python
def build_review_prompt(report, skip, severity):
    """report/skip: lists of categories. severity: {level: definition_with_example}."""
    report_lines = "\n".join(f"- {c}" for c in report)
    skip_lines = "\n".join(f"- {c}" for c in skip)
    sev_lines = "\n".join(f"- {lvl}: {definition}" for lvl, definition in severity.items())
    return f"""You are a code reviewer. Apply these criteria exactly.

REPORT issues only in these categories:
{report_lines}

Do NOT report (skip silently):
{skip_lines}

Assign severity using these definitions:
{sev_lines}

Flag an issue only when it clearly meets one of the REPORT categories above.
Do not filter by confidence and do not invent categories — if it isn't listed
above, skip it."""

prompt = build_review_prompt(
    report=["Bugs: code that produces incorrect behavior",
            "Security: injection, auth bypass, secret leakage"],
    skip=["Minor style (formatting, naming)", "Local conventions you can't verify"],
    severity={
        "critical": "data loss, security breach, or crash on common input "
                    "(e.g. unsanitized SQL string interpolation)",
        "minor": "correctness issue with low blast radius (e.g. off-by-one in a log line)",
    },
)
```

Every decision the model has to make is pinned to something written down: which categories count, which don't, and what each severity means with an example. There's no "use your judgment about confidence" left in the prompt.

## Anti-patterns & pitfalls

1. **Confidence-based filtering instead of criteria.** "Be conservative," "only report high-confidence findings," "use your best judgment." These read like precision controls but aren't — they don't define the boundary, so the model picks one, and it drifts. The exam is explicit that general instructions like these "fail to improve precision compared to specific categorical criteria." Replace the confidence dial with a definition.
2. **Naming what to find but not what to skip.** "Find security issues" without "skip X, Y, Z" leaves a gray zone the model fills with false positives. Define both sides.
3. **Severity labels without anchors.** `critical`/`major`/`minor` with no concrete example per level produces inconsistent classification across runs. Anchor each level to example code.
4. **One noisy category poisoning trust in the rest.** A single high-false-positive category "undermines confidence in accurate categories" — developers mute the whole tool. The fix is to sharpen (or temporarily disable) *that* category, not to globally dial down sensitivity.

The prescribed move is always the same: **turn the vague instruction into an explicit, categorical criterion with concrete examples.** "Be more careful" is never the answer on this exam.

## Exam focus

This task statement underpins the precision questions in **CCAF Scenario 2 (Code Generation with Claude Code)** and **Scenario 5 (Claude Code for CI)** — both feature review agents whose value collapses when false positives erode developer trust. The distractor to reject is always the confidence-based filter ("be conservative," "high-confidence only"); the correct answer is the specific categorical criterion.

## References & further reading

- [Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) — why a clear definition of success criteria comes *before* prompt engineering.
- [Prompting best practices — Be clear and direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — explicit, specific instructions; the "confused colleague" golden rule; adding context/motivation.

## Exam coverage

- **CCAF** — Domain 4 (Prompt Engineering & Structured Output), Task Statement 4.1: Design prompts with explicit criteria to improve precision and reduce false positives.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
