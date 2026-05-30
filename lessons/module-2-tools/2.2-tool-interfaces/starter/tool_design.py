"""Starter skeleton for Learn Claude chapter 2.2 — Designing tool interfaces.

Implement the two functions below. See exercise.md for the full spec.
These are pure logic — no Anthropic API, no API key, no network.
"""

import re

NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def lint_tool_definition(tool: dict) -> list:
    """Return a list of issue codes for a tool definition (empty list == clean).

    Issue codes:
      "name_invalid"
      "description_missing"            (absent or blank)
      "description_too_thin"           (present but fewer than 3 sentences)
      "param_missing_description:<p>"  (per undescribed property)
      "required_not_in_properties:<r>" (per bogus required entry)

    Emit description_missing OR description_too_thin, never both.
    """
    # TODO: implement.
    #   - Validate tool["name"] against NAME_RE.
    #   - Check the description: blank -> description_missing; otherwise count
    #     sentences (split on . ! ?) and flag description_too_thin if < 3.
    #   - For each property in input_schema["properties"], require a non-empty
    #     "description".
    #   - For each name in input_schema["required"], require it to be a declared
    #     property.
    raise NotImplementedError("Implement lint_tool_definition — see exercise.md")


def first_fix_for(symptom: str) -> str:
    """Map a tool-use failure symptom to the prescribed FIRST remedy.

      "wrong_tool_selected"             -> "improve_description"
      "missing_required_parameter"      -> "improve_description"
      "too_many_overlapping_tools"      -> "consolidate_tools"
      "ambiguous_names_across_services" -> "add_namespacing"
      "responses_bloat_context"         -> "shape_responses"

    Raise ValueError for an unknown symptom.
    """
    # TODO: implement. Note: the first fix for wrong_tool_selected is improving
    #   the tool DESCRIPTION — not adding few-shot examples to the prompt.
    raise NotImplementedError("Implement first_fix_for — see exercise.md")
