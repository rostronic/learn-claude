"""Tests for the structured-output helpers. The response is mocked — no API key needed."""

from types import SimpleNamespace

import pytest

from structured_output import extraction_tool, force_tool_choice, parse_tool_result


def _tool_use(name, data):
    return SimpleNamespace(type="tool_use", id="toolu_1", name=name, input=data)


def _text(text):
    return SimpleNamespace(type="text", text=text)


def _response(content):
    return SimpleNamespace(stop_reason="tool_use", content=content)


def test_extraction_tool_shape():
    props = {"vendor": {"type": "string"}, "total": {"type": "number"}}
    tool = extraction_tool("record_invoice", props, ["vendor", "total"])
    assert tool["name"] == "record_invoice"
    assert "description" in tool
    schema = tool["input_schema"]
    assert schema["type"] == "object"
    assert schema["properties"] == props
    assert schema["required"] == ["vendor", "total"]


def test_force_tool_choice():
    assert force_tool_choice("record_invoice") == {"type": "tool", "name": "record_invoice"}


def test_parse_returns_tool_use_input():
    resp = _response([
        _text("Here you go:"),
        _tool_use("record_invoice", {"vendor": "Acme", "total": 42.0}),
    ])
    data = parse_tool_result(resp, "record_invoice")
    assert data == {"vendor": "Acme", "total": 42.0}


def test_parse_raises_when_model_returns_text_only():
    """No tool_use block -> raise, do NOT scrape JSON from the text."""
    resp = _response([_text('{"vendor": "Acme", "total": 42}')])
    with pytest.raises(ValueError):
        parse_tool_result(resp, "record_invoice")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
