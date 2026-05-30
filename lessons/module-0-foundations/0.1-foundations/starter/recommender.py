"""Starter skeleton for Learn Claude chapter 0.1 — Foundations.

Implement recommend_technology below. See exercise.md for the full spec.

This is a pure-logic exercise: no Anthropic API calls, no network. You are
encoding the decision tree from the lesson — given a task's signals, name the
primary technology to reach for first.
"""

# The four technologies this course is about, as stable string keys.
TECHNOLOGIES = ("messages_api", "agent_sdk", "claude_code", "mcp")

# One-line orientation for each — what it is, in the lesson's words.
EXPLANATIONS = {
    "messages_api": (
        "Direct, stateless model access: one request, one response. "
        "You build any loop yourself."
    ),
    "agent_sdk": (
        "Runs the agent loop for you inside your own Python/TypeScript "
        "process, with Claude Code's tools and context management."
    ),
    "claude_code": (
        "The agentic coding harness a developer drives in the terminal, "
        "IDE, desktop app, or browser."
    ),
    "mcp": (
        "An open standard that connects Claude to external tools and data "
        "sources (databases, issue trackers, APIs)."
    ),
}


def recommend_technology(task):
    """Given a task's signals, name the primary technology to reach for.

    Args:
        task: dict of boolean signals. Recognized keys:
            connect_external_system  — the need is to connect Claude to an
                                       outside system (DB, tracker, API).
            interactive_coding       — a developer is coding interactively in
                                       a terminal/IDE (or automating coding).
            needs_autonomous_loop    — an autonomous multi-step agent must run
                                       inside your own application/process.
            Any missing key is treated as False.

    Returns:
        One of TECHNOLOGIES — the primary technology to reach for first.
    """
    # TODO: implement, checking the signals in priority order.
    #   1. connect_external_system  -> "mcp"
    #   2. interactive_coding        -> "claude_code"
    #   3. needs_autonomous_loop     -> "agent_sdk"
    #   4. otherwise                 -> "messages_api"   <-- the floor.
    #
    # The fallback (no special signal set) MUST be "messages_api": a single
    # model call is enough, so do NOT default to the heavier Agent SDK.
    raise NotImplementedError("Implement recommend_technology — see exercise.md")
