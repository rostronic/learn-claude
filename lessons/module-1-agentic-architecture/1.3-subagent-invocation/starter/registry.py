"""Subagent registry (AgentDefinitions) and accepted spawn-tool names for Lesson 1.3.

Each registry entry is an AgentDefinition-shaped dict: a `description` (when to use it),
a `prompt` (the subagent's own system prompt), and an optional `tools` list (allowed
tool names; omit to inherit all tools).
"""

# A coordinator can spawn subagents only if one of these is in its allowed_tools.
# The exam guide names the tool "Task"; current SDK releases emit "Agent" (it was
# renamed in Claude Code v2.1.63). Accept either name.
SPAWN_TOOLS = {"Task", "Agent"}

AGENT_REGISTRY = {
    "researcher": {
        "description": "Researches one focused subtopic and returns concise, sourced facts.",
        "prompt": "You are a research specialist. Return concise, well-sourced facts.",
        "tools": ["Read", "Grep", "Glob", "WebSearch"],   # restricted: no Edit/Write/Bash
    },
    "synthesizer": {
        "description": "Merges findings from prior agents into one coherent, cited answer.",
        "prompt": "You merge findings from multiple sources into one coherent, cited answer.",
        # No "tools" key: the synthesizer inherits all tools.
    },
}
