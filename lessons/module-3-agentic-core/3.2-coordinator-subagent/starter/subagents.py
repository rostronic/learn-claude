"""Subagent tool schemas and an isolated spawner for chapter 3.2.

The schemas (RESEARCHER, SYNTHESIZER) are the shape the coordinator passes in the
`tools` parameter of client.messages.create() — each subagent is a "tool" the
coordinator may invoke. spawn_subagent() runs a subagent in ISOLATED context: it
receives ONLY the `task` string the coordinator composed, never the coordinator's
conversation history.
"""

import anthropic

# Each subagent exposes a single required input, "task" — the coordinator fills it
# in per invocation. That string is the ONLY context the subagent ever sees.
RESEARCHER = {
    "name": "researcher",
    "description": (
        "Researches one focused subtopic and returns a short factual summary. "
        "Invoke once per distinct subtopic; do not use it for final synthesis."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The specific subtopic to research, stated self-containedly.",
            },
        },
        "required": ["task"],
    },
}

SYNTHESIZER = {
    "name": "synthesizer",
    "description": (
        "Merges research findings into one coherent, cited answer. Pass the findings "
        "to merge (and the original question) in the task."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The findings to merge plus the original question.",
            },
        },
        "required": ["task"],
    },
}

# A subagent's OWN system prompt — its specialized instructions. This is the only
# standing context it has; everything task-specific arrives via `task`.
_SUBAGENT_PROMPTS = {
    "researcher": "You are a research specialist. Summarize the key facts concisely and factually.",
    "synthesizer": "You merge findings from multiple sources into one coherent, cited answer.",
}


def spawn_subagent(name: str, task: str) -> str:
    """Run the named subagent in ISOLATED context and return its final text.

    The subagent gets a fresh conversation seeded with ONLY `task`. It does not see
    the coordinator's history or any other subagent's work — that is the point of
    hub-and-spoke context isolation.
    """
    sub = anthropic.Anthropic()
    response = sub.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SUBAGENT_PROMPTS[name],
        messages=[{"role": "user", "content": task}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
