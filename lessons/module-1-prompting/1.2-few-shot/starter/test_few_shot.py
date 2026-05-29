"""Tests for build_few_shot_prompt. Pure logic — no API key, no model calls."""

import pytest

from few_shot import build_few_shot_prompt

DIVERSE = [
    {"input": "# returns age\ndef get_name(u): return u.name", "output": "BUG", "label": "BUG"},
    {"input": "# fast path\nif cached: return cached", "output": "OK", "label": "OK"},
]


def test_raises_with_fewer_than_two_examples():
    with pytest.raises(ValueError):
        build_few_shot_prompt("Classify.", [DIVERSE[0]])


def test_raises_on_single_class_examples():
    same_label = [
        {"input": "a", "output": "BUG", "label": "BUG"},
        {"input": "b", "output": "BUG", "label": "BUG"},
    ]
    with pytest.raises(ValueError):
        build_few_shot_prompt("Classify.", same_label)


def test_examples_are_wrapped_and_complete():
    prompt = build_few_shot_prompt("Classify each comment.", DIVERSE)
    assert "Classify each comment." in prompt
    assert "<examples>" in prompt and "</examples>" in prompt
    assert prompt.count("<example>") == len(DIVERSE)
    for e in DIVERSE:
        assert e["input"] in prompt
        assert e["output"] in prompt


def test_examples_without_labels_are_allowed():
    """Diversity is only enforced when labels are provided."""
    unlabeled = [{"input": "a", "output": "x"}, {"input": "b", "output": "y"}]
    prompt = build_few_shot_prompt("Do the thing.", unlabeled)
    assert prompt.count("<example>") == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
