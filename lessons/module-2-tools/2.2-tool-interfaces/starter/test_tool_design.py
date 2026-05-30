"""Tests for the tool-interface design toolkit. Pure logic — no API key needed."""

import pytest

from tool_design import first_fix_for, lint_tool_definition

# A well-formed tool, modeled on the docs' "good" get_stock_price example.
GOOD_TOOL = {
    "name": "get_stock_price",
    "description": (
        "Retrieves the current stock price for a given ticker symbol. The ticker "
        "must be a valid symbol on a major US exchange like NYSE or NASDAQ. It "
        "returns the latest trade price in USD. Use it when the user asks for the "
        "current or most recent price of a specific stock."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {"type": "string", "description": "The ticker symbol, e.g. AAPL."}
        },
        "required": ["ticker"],
    },
}


def test_good_tool_is_clean():
    assert lint_tool_definition(GOOD_TOOL) == []


def test_thin_description_flagged():
    tool = {**GOOD_TOOL, "description": "Gets the stock price for a ticker."}
    assert "description_too_thin" in lint_tool_definition(tool)


def test_missing_description_flagged():
    tool = {**GOOD_TOOL, "description": "   "}
    issues = lint_tool_definition(tool)
    assert "description_missing" in issues
    assert "description_too_thin" not in issues  # one or the other, not both


def test_invalid_name_flagged():
    tool = {**GOOD_TOOL, "name": "get stock price!"}  # spaces + '!' are invalid
    assert "name_invalid" in lint_tool_definition(tool)


def test_undocumented_parameter_flagged():
    tool = {
        **GOOD_TOOL,
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},  # no description
            "required": ["ticker"],
        },
    }
    assert "param_missing_description:ticker" in lint_tool_definition(tool)


def test_required_not_in_properties_flagged():
    tool = {
        **GOOD_TOOL,
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string", "description": "Ticker."}},
            "required": ["ticker", "exchange"],  # exchange is not a property
        },
    }
    assert "required_not_in_properties:exchange" in lint_tool_definition(tool)


@pytest.mark.parametrize(
    "symptom,expected",
    [
        ("wrong_tool_selected", "improve_description"),
        ("missing_required_parameter", "improve_description"),
        ("too_many_overlapping_tools", "consolidate_tools"),
        ("ambiguous_names_across_services", "add_namespacing"),
        ("responses_bloat_context", "shape_responses"),
    ],
)
def test_first_fix_mapping(symptom, expected):
    assert first_fix_for(symptom) == expected


def test_wrong_tool_fix_is_not_few_shot():
    """The exam's headline rule: fix the description, not the prompt's examples."""
    fix = first_fix_for("wrong_tool_selected")
    assert fix == "improve_description"
    assert "few_shot" not in fix and "example" not in fix


def test_unknown_symptom_raises():
    with pytest.raises(ValueError):
        first_fix_for("cosmic_rays")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
