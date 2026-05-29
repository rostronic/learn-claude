"""Starter skeleton for Learn Claude chapter 1.2 — Few-shot prompting.

Implement build_few_shot_prompt below. See exercise.md for the full spec.
"""


def build_few_shot_prompt(instruction, examples):
    """Assemble a structured few-shot prompt.

    Args:
        instruction: str — the task instruction.
        examples:    list[dict] — each {"input": str, "output": str, "label": str (optional)}.

    Returns:
        str — instruction + examples wrapped in <example> tags inside an <examples> block.

    Raises:
        ValueError if fewer than 2 examples, or if labels are present and all identical.
    """
    # TODO: implement
    #   1. Raise ValueError if len(examples) < 2.
    #   2. If every example has a "label" and they're all the same, raise ValueError
    #      (single-class examples aren't diverse).
    #   3. Wrap each example's input/output in <example> tags inside one <examples>
    #      block, and return the instruction followed by that block.
    raise NotImplementedError("Implement build_few_shot_prompt — see exercise.md")
