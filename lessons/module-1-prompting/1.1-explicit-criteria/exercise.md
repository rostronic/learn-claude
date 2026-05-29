# Prompting with explicit criteria — exercise

## What you're building

Implement `build_review_prompt` in `prompt_builder.py`. It assembles a code-review prompt from **explicit, categorical criteria** — the categories to report, the categories to skip, and severity levels anchored to concrete examples — and refuses to build a vague one.

This is pure logic — no API calls. You're constructing the prompt string a review agent would run.

## Function signature

```python
def build_review_prompt(report, skip, severity):
    """
    Args:
        report:   list[str] — categories the reviewer MUST report (non-empty).
        skip:     list[str] — categories the reviewer MUST skip (non-empty).
        severity: dict[str, str] — {level: definition}; each definition should anchor
                  the level to a concrete example (non-empty).

    Returns:
        str — a prompt that lists the report categories, the skip categories, the
        severity definitions, and an explicit instruction to flag by criteria (not by
        confidence).

    Raises:
        ValueError if `report`, `skip`, or `severity` is empty.
    """
```

## Requirements

You must:

1. **Force explicitness.** Raise `ValueError` if `report`, `skip`, or `severity` is empty — you cannot build a precise prompt without stating both what to flag and what to skip.
2. **Include every category and severity** in the returned prompt: each `report` entry, each `skip` entry, and each `severity` level with its definition.
3. **Instruct flagging by criteria, not confidence.** The prompt must tell the model to flag an issue only when it clearly meets a listed REPORT category — not to "be conservative" or filter by confidence.
4. **Pass every test in `test_prompt_builder.py`.**

You must NOT:

5. **Inject vague, confidence-based instructions** as a substitute for explicit criteria — no "be conservative", "use your judgment", or "only high-confidence findings" baked into the prompt. Precision comes from the categorical criteria, not a confidence dial.

Requirement 5 is graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/1.1
pip install -r requirements.txt
pytest -v
```

No `ANTHROPIC_API_KEY` needed — the exercise is pure logic.

When you're ready (or stuck), run `/verify 1.1` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first.
- [Prompting best practices — Be clear and direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — explicit, specific instructions.
