"""Tests for the three hook callbacks. Pure logic — no SDK, no network, no key.

Each input_data dict mirrors the shape the Agent SDK passes to a hook callback.
"""

import pytest

from hooks import guard_secrets, normalize_output, redirect_write


def _pre(tool_name, **tool_input):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


def _post(tool_name, response):
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_response": response,
    }


# --- guard_secrets (PreToolUse, block) ---

def test_guard_blocks_write_to_dotenv():
    decision = guard_secrets(_pre("Write", file_path="/app/.env", content="SECRET=1"))
    hso = decision["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert isinstance(hso["permissionDecisionReason"], str) and hso["permissionDecisionReason"]


def test_guard_blocks_edit_to_dotenv():
    decision = guard_secrets(_pre("Edit", file_path="/srv/config/.env"))
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_guard_allows_non_dotenv_write():
    # Same tool, different argument — proves the decision inspects the file_path,
    # not just the tool name (matchers only filter by tool name).
    assert guard_secrets(_pre("Write", file_path="/app/config.yaml")) == {}


def test_guard_allows_non_write_tool():
    assert guard_secrets(_pre("Read", file_path="/app/.env")) == {}


# --- normalize_output (PostToolUse, transform) ---

def test_normalize_lowercases_keys_and_defaults_units():
    decision = normalize_output(_post("get_weather", {"Temperature": 68, "Conditions": "clear"}))
    out = decision["hookSpecificOutput"]["updatedToolOutput"]
    assert decision["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert out == {"temperature": 68, "conditions": "clear", "units": "fahrenheit"}


def test_normalize_is_idempotent_on_canonical_input():
    canonical = {"temperature": 68, "conditions": "clear", "units": "fahrenheit"}
    assert normalize_output(_post("get_weather", canonical)) == {}


def test_normalize_keeps_existing_units():
    decision = normalize_output(_post("get_weather", {"Temperature": 20, "units": "celsius"}))
    out = decision["hookSpecificOutput"]["updatedToolOutput"]
    assert out["units"] == "celsius"
    assert out["temperature"] == 20


# --- redirect_write (PreToolUse, modify input) ---

def test_redirect_prefixes_path_and_allows():
    original = {"file_path": "/app/out.txt", "content": "hi"}
    input_data = _pre("Write", **original)
    decision = redirect_write(input_data)
    hso = decision["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert hso["updatedInput"]["file_path"] == "/sandbox/app/out.txt"
    assert hso["updatedInput"]["content"] == "hi"


def test_redirect_does_not_mutate_original_tool_input():
    input_data = _pre("Write", file_path="/app/out.txt", content="hi")
    redirect_write(input_data)
    # The original tool_input must be untouched (return a NEW dict).
    assert input_data["tool_input"]["file_path"] == "/app/out.txt"


def test_redirect_ignores_non_write_tools():
    assert redirect_write(_pre("Read", file_path="/app/out.txt")) == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
