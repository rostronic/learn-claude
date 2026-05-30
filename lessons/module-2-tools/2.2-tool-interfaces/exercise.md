# Designing tool interfaces — exercise

## What you're building

Two pieces of an interface-design toolkit in `tool_design.py`:

1. `lint_tool_definition(tool)` — a structural linter that flags the ways a tool definition violates the Define-tools best practices (bad name, thin/missing description, undocumented parameters, bogus `required` entries).
2. `first_fix_for(symptom)` — a decision function that, given a tool-use failure symptom, returns Anthropic's prescribed **first** remedy.

This is CCAF Task Statement 2.1 in code: clear descriptions and clear boundaries, and knowing that the first fix for a selection problem is the *description* — not few-shot examples.

No Anthropic API is involved — the tests are pure logic and need no `ANTHROPIC_API_KEY`.

## Functions to implement

```python
def lint_tool_definition(tool: dict) -> list[str]:
    """Return a list of issue codes for a tool definition (empty list == clean).

    Issue codes to emit:
      "name_invalid"                  - name missing or not matching ^[a-zA-Z0-9_-]{1,64}$
      "description_missing"           - description absent or blank
      "description_too_thin"          - description present but fewer than 3 sentences
                                        (docs: aim for at least 3-4 sentences)
      "param_missing_description:<p>" - property <p> in input_schema has no description
      "required_not_in_properties:<r>"- required name <r> is not a declared property

    A description is "thin" if it has fewer than 3 sentences (split on . ! ?).
    Emit description_missing OR description_too_thin, not both.
    """

def first_fix_for(symptom: str) -> str:
    """Map a tool-use failure symptom to the prescribed FIRST remedy.

      "wrong_tool_selected"             -> "improve_description"
      "missing_required_parameter"      -> "improve_description"
      "too_many_overlapping_tools"      -> "consolidate_tools"
      "ambiguous_names_across_services" -> "add_namespacing"
      "responses_bloat_context"         -> "shape_responses"
    Raise ValueError for an unknown symptom.
    """
```

## Requirements

You must:

1. **Validate the name** against `^[a-zA-Z0-9_-]{1,64}$` and emit `name_invalid` when it fails or is absent.
2. **Enforce description quality** — emit `description_missing` for an absent/blank description, and `description_too_thin` for a present description with fewer than 3 sentences. This is the most important check: the description is by far the biggest factor in tool performance.
3. **Flag undocumented parameters** — emit `param_missing_description:<p>` for every property lacking a non-empty `description`.
4. **Flag bogus required entries** — emit `required_not_in_properties:<r>` for any `required` name that isn't a declared property.
5. **Return a clean (empty) list** for a well-formed tool (good name, 3+ sentence description, every parameter described, valid `required`).
6. **Map symptoms to the prescribed first fix** in `first_fix_for`, and raise `ValueError` on an unknown symptom.
7. **Pass every test in `test_tool_design.py`.**

You must NOT:

8. **Recommend few-shot examples as the first fix for wrong tool selection.** `first_fix_for("wrong_tool_selected")` must return `"improve_description"` — never an examples/few-shot answer. The exam's prescribed first fix for a tool-selection failure is a better tool *description*, not exemplars added to the prompt. This is graded directly (`check: anti_pattern`).

## How to run it

```bash
cd ~/learn-claude-work/2.2
pip install -r requirements.txt
pytest -v
```

The tests are pure logic — no API key, no network, no credits burned.

When you're ready (or stuck), run `/verify 2.2` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) — the best-practices list this linter encodes, plus the good-vs-poor description examples.
