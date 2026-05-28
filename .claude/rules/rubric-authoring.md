---
paths: ["lessons/**/rubric.yaml"]
---

# Rubric authoring rules

These rules load whenever you edit a `rubric.yaml` under `lessons/`. They build on the editorial constitution in the root [CLAUDE.md](../../CLAUDE.md).

## Schema

```yaml
task_statement: "<exact ID and title from the CCA-F exam guide>"
exam_guide_reference: "Domain <N>, Task Statement <X.Y>"
criteria:
  - id: <snake_case_unique_id>
    description: "<a specific, checkable assertion about the user's code>"
    weight: <integer>           # weights across all criteria must sum to 100
    check: code_review | anti_pattern | bash_execution
    command: "<shell command>"  # required iff check == bash_execution
```

## Field rules

- **`task_statement`** — verbatim from the exam guide, ID and full title. Same string as the opening header of the matching `lesson.md`.
- **`exam_guide_reference`** — domain number and task statement ID. Lets the verifier and the user trace a failing criterion back to the source.
- **`criteria[].id`** — `snake_case`. Stable identifier; the Phase 2 verifier and Phase 4 progress tracker will key off these, so don't rename them once published.
- **`criteria[].description`** — must be **specific enough that a verifier can check it by reading the user's code** (or by reading `pytest` output, for `bash_execution`). See "Specificity" below.
- **`criteria[].weight`** — integer percentage. **Weights across all criteria must sum to exactly 100.**
- **`criteria[].check`** — one of three dispatch types. See "Check types" below.
- **`criteria[].command`** — required only when `check: bash_execution`. The exact command the verifier will run (Phase 1: a human does this; Phase 2: the grading MCP server).

## Required: at least one `anti_pattern` criterion

**Every rubric must include at least one criterion with `check: anti_pattern`** — something the user must NOT do. This is non-negotiable and mirrors how the CCA-F exam itself works (distractors are wrong patterns candidates with incomplete knowledge would choose).

If you can't think of an anti-pattern for the topic you're rubricizing, re-read the relevant task statement in the exam guide — its "Skills in:" section almost always lists "Avoiding anti-patterns such as…". Lift those directly.

## Check types

- **`code_review`** — verifier reads the user's source and judges whether the criterion is met. Use for structural / behavioral assertions about the code itself.
- **`anti_pattern`** — verifier reads the user's source looking for the *presence* of a forbidden pattern. Fails if the pattern is present. Phrase the `description` as what the user must NOT do.
- **`bash_execution`** — verifier runs the given `command` in the user's work directory; pass iff exit code is 0. Use for test suites, linters, or anything with a binary outcome.

## Specificity

Vague criteria are unverifiable and useless. Drop these:

- ❌ "Uses good practices"
- ❌ "Handles errors appropriately"
- ❌ "Code is well-structured"

Write these instead:

- ✅ "Loop continues when `stop_reason` is `'tool_use'`"
- ✅ "Does NOT inspect assistant text content as a termination signal"
- ✅ "All tests in `test_agentic_loop.py` pass" (with `check: bash_execution`)

The test: can someone with the user's code in front of them give an unambiguous pass/fail in under 30 seconds? If no, rewrite.
