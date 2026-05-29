"""Starter skeleton for Learn Claude chapter 1.3 — Structured output with tool use.

Implement the three helpers below. See exercise.md for the full spec.
"""


def extraction_tool(name, properties, required):
    """Build a Claude tool whose input_schema IS your output shape.

    Returns {"name", "description", "input_schema"} where input_schema is a
    JSON-schema object: {"type": "object", "properties": properties, "required": required}.
    """
    # TODO: implement
    raise NotImplementedError("Implement extraction_tool — see exercise.md")


def force_tool_choice(name):
    """Return the tool_choice that forces the named tool: {"type": "tool", "name": name}."""
    # TODO: implement
    raise NotImplementedError("Implement force_tool_choice — see exercise.md")


def parse_tool_result(response, tool_name):
    """Return the structured input dict from the matching tool_use block.

    Iterate response.content; return the .input of the tool_use block whose .name
    == tool_name. Raise ValueError if there is no such block (the model returned
    text) — do NOT parse JSON out of free text.
    """
    # TODO: implement
    raise NotImplementedError("Implement parse_tool_result — see exercise.md")
