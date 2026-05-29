# Few-shot prompting — exercise

## What you're building

Implement `build_few_shot_prompt` in `few_shot.py`. It assembles a structured few-shot prompt from an instruction plus examples, and enforces the two properties that make few-shot actually work: **enough examples** and **more than one class** represented.

Pure logic — no API calls.

## Function signature

```python
def build_few_shot_prompt(instruction, examples):
    """
    Args:
        instruction: str — the task instruction.
        examples:    list[dict] — each {"input": str, "output": str, "label": str (optional)}.

    Returns:
        str — instruction followed by the examples, each wrapped in <example> tags
        inside an <examples> block.

    Raises:
        ValueError if fewer than 2 examples.
        ValueError if labels are present and every example has the SAME label
                   (single-class — not diverse).
    """
```

## Requirements

You must:

1. **Require a real set.** Raise `ValueError` if fewer than 2 examples.
2. **Require diversity when labels are given.** If every example carries a `label` and they're all identical, raise `ValueError` — single-class examples teach the model to always answer that way.
3. **Structure the examples.** Wrap each example in `<example>` tags (with its input and output) inside a single `<examples>` block, after the instruction.
4. **Include every example's input and output** in the returned prompt.
5. **Pass every test in `test_few_shot.py`.**

You must NOT:

6. **Accept single-class / non-diverse example sets** as valid (when labels are provided). Diversity — contrasting cases, not all one label — is what lets the model generalize instead of pattern-matching, and is what keeps false positives down.

Requirement 6 is graded directly by the rubric (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/1.2
pip install -r requirements.txt
pytest -v
```

No `ANTHROPIC_API_KEY` needed — the exercise is pure logic.

When you're ready (or stuck), run `/verify 1.2` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first.
- [Prompting best practices — Use examples effectively](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — relevant, diverse, structured examples.
