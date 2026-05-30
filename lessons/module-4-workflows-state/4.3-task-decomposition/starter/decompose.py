"""Starter skeleton for Learn Claude chapter 4.3 — Task decomposition strategies.

Implement `decompose`, `validate_plan`, and `parallel_batches` below. These model
the planning logic of splitting a complex task into well-scoped subagents: what
runs in parallel vs. sequentially (by dependency), and least-privilege tools per
subagent. Each subagent spec is a plain dict standing in for an Agent SDK
AgentDefinition. See exercise.md for the full spec.
"""

# Least-privilege tool sets.
READ_ONLY = ["Read", "Grep", "Glob"]
TEST_RUNNER = ["Bash", "Read", "Grep"]


def decompose(task: str) -> list:
    """Break a known complex task into an ordered list of subtask specs.

    For the PR-review task, return three independent read-only finders
    (style-checker, security-scanner, test-runner) in parallel_group 0 with
    depends_on [], plus a synthesis step in parallel_group 1 that depends on all
    three. The test-runner gets TEST_RUNNER tools; the other finders get
    READ_ONLY; synthesis gets READ_ONLY. NEVER include "Agent" in any spec's
    tools (subagents cannot spawn subagents).

    Each spec is a dict:
        {"name": str,
         "tools": list[str],
         "depends_on": list[str],
         "parallel_group": int}
    """
    # TODO: implement
    #   - Build the four specs described above.
    #   - Finders: parallel_group 0, depends_on [].
    #   - Synthesis: parallel_group 1, depends_on the three finder names.
    #   - Read-only finders get READ_ONLY; test-runner gets TEST_RUNNER.
    #   - No spec's tools may contain "Agent".
    raise NotImplementedError("Implement decompose — see exercise.md")


def validate_plan(plan: list) -> list:
    """Return a list of human-readable problems with a plan (empty list = valid).

    Flag each of:
      - a spec whose tools include "Agent" (subagents can't spawn subagents);
      - a depends_on entry referencing a subtask name not in the plan;
      - a dependency inversion: a spec depends_on another spec in a LATER or the
        SAME parallel_group (a dependency must finish in an EARLIER batch).
    """
    # TODO: implement
    #   - Build a name -> spec index.
    #   - For each spec, check the three conditions above and append a message
    #     describing any problem found.
    #   - Return the (possibly empty) list of problem strings.
    raise NotImplementedError("Implement validate_plan — see exercise.md")


def parallel_batches(plan: list) -> list:
    """Group subtask names into ordered batches by parallel_group.

    Returns a list of lists: batch i (parallel_group i) runs after batch i-1.
    Within a batch the order does not matter, but return names in the order they
    appear in `plan` for determinism. Example:
        [["style-checker", "security-scanner", "test-runner"], ["synthesis"]]
    """
    # TODO: implement
    #   - Find the distinct parallel_group values, sorted ascending.
    #   - For each group, collect the names of specs in that group (in plan order).
    raise NotImplementedError("Implement parallel_batches — see exercise.md")
