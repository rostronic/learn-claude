"""Starter skeleton for Learn Claude chapter 4.2 — Agent SDK hooks for tool
interception & data normalization.

Implement the three hook callbacks below. Each models the real Agent SDK hook
contract: an `input_data` dict in, a decision/transform dict out. The SDK passes
these exact dicts to a callback registered as
`HookMatcher(matcher=..., hooks=[callback])`; here you write and test the pure
logic with no SDK or network involved.

See exercise.md for the full spec.
"""

import os

# Tools that can write to the filesystem (the ones a secrets guard cares about).
WRITE_TOOLS = {"Write", "Edit"}


def guard_secrets(input_data: dict, tool_use_id=None, context=None) -> dict:
    """PreToolUse hook: block writes to a .env file.

    Deny when tool_name is a write tool AND tool_input['file_path'] names a .env
    file (basename '.env'). Return {} otherwise.

    Deny shape:
        {"hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "deny",
            "permissionDecisionReason": <str>}}
    """
    # TODO: implement
    #   - Read tool_name and tool_input from input_data.
    #   - Matchers only filter by TOOL NAME, so you must inspect the file_path
    #     ARGUMENT here. Use os.path.basename(file_path) == ".env".
    #   - Return the deny object when it's a write to .env; otherwise {}.
    raise NotImplementedError("Implement guard_secrets — see exercise.md")


def normalize_output(input_data: dict, tool_use_id=None, context=None) -> dict:
    """PostToolUse hook: normalize a tool result to a canonical shape.

    Given input_data with a 'tool_response' dict, return a canonical version via
    updatedToolOutput. Canonical form: all top-level keys lowercased, and a
    'units' key defaulting to 'fahrenheit' if absent.

        {"hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "updatedToolOutput": <canonical dict>}}

    Return {} if the response is already canonical (nothing to change).
    """
    # TODO: implement
    #   - Read the response dict from input_data["tool_response"].
    #   - Build canonical = {k.lower(): v for k, v in response.items()},
    #     adding "units": "fahrenheit" if missing.
    #   - If canonical == response, return {} (idempotent — no change needed).
    #   - Else return the updatedToolOutput wrapper.
    raise NotImplementedError("Implement normalize_output — see exercise.md")


def redirect_write(input_data: dict, tool_use_id=None, context=None) -> dict:
    """PreToolUse hook: redirect Write calls into a /sandbox prefix.

    For a Write call, return an ALLOW decision plus updatedInput whose file_path
    is the original prefixed with '/sandbox'. updatedInput must be a NEW dict;
    do not mutate input_data['tool_input'].

        {"hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "allow",
            "updatedInput": {... "file_path": "/sandbox" + original ...}}}

    Return {} for non-Write tools.
    """
    # TODO: implement
    #   - Only act when tool_name == "Write"; else {}.
    #   - Build a NEW dict from tool_input with file_path prefixed by "/sandbox".
    #   - Return hookSpecificOutput with permissionDecision "allow" AND updatedInput.
    #     (updatedInput is ignored unless permissionDecision is "allow" or "ask".)
    raise NotImplementedError("Implement redirect_write — see exercise.md")
