---
chapter: "6.4"
slug: "capstone-ci"
title: "Capstone — Claude Code for Continuous Integration"
module: "module-6-extraction-quality"
sequence: 27
references:
  - title: "Run Claude Code programmatically (headless)"
    url: "https://code.claude.com/docs/en/headless"
    type: official_docs
    covers: "claude -p non-interactive mode, --allowedTools, --output-format json, --bare for CI"
  - title: "GitHub Actions"
    url: "https://code.claude.com/docs/en/github-actions"
    type: official_docs
    covers: "Running the Agent SDK / Claude Code inside a CI workflow"
  - title: "Batch processing (Message Batches API)"
    url: "https://platform.claude.com/docs/en/build-with-claude/batch-processing"
    type: official_docs
    covers: "50% cost, 24h window/no SLA — when a CI job belongs in batch vs synchronous"
  - title: "Create custom subagents"
    url: "https://code.claude.com/docs/en/sub-agents"
    type: official_docs
    covers: "Independent reviewer instances for catching issues self-review misses"
---

# Capstone — Claude Code for Continuous Integration

## Overview

This is a capstone: a single applied scenario that pulls together the threads of this module and Module 5 into one production system. The scenario is **CCAF Exam Scenario 5** — "integrating Claude Code into your CI/CD pipeline" to run "automated code reviews, generate test cases, and provide feedback on pull requests," where the explicit goal is "prompts that provide actionable feedback and minimize false positives."

Nothing here is a brand-new concept. The point of a capstone is *integration*: seeing how four task statements you've learned separately combine, and where they trade against each other in one pipeline. Concretely, a CI review system has to answer four questions, each owned by a task statement you've already studied:

- **How do we run Claude Code with no human present?** — non-interactive (headless) Claude Code (CCAF 3.6).
- **Which jobs run now, and which run cheaply overnight?** — synchronous vs. the Batches API (CCAF 4.5, [chapter 6.2](../6.2-batch-processing/lesson.md)).
- **How do we review a multi-file PR well?** — independent, multi-pass review (CCAF 4.6, [chapter 6.3](../6.3-multi-instance-review/lesson.md)).
- **How do we keep developers from ignoring the bot?** — explicit categorical criteria to minimize false positives (CCAF 4.1), backed by validation (CCAF 4.4, [chapter 6.1](../6.1-validation-retry-loops/lesson.md)).

We'll build a compact pipeline that wires all four together.

## How it works

### Running Claude Code in CI (3.6)

CI has no human to approve a permission prompt, so an interactive invocation **hangs forever** waiting on input that never comes. The fix is to run headless: pass `-p` (a.k.a. `--print`), which runs Claude Code non-interactively — it processes the prompt, prints the result to stdout, and exits without waiting on input ([Run Claude Code programmatically](https://code.claude.com/docs/en/headless)). You pre-authorize exactly the tools the job needs with `--allowedTools`, and ask for parseable output with `--output-format json`:

```bash
claude -p "Review this diff for security issues" \
  --allowedTools "Read,Grep" \
  --output-format json
```

Two things this is *not*: it's not `CLAUDE_HEADLESS=true` or a `--batch` flag (those don't exist), and it's emphatically not reaching for `--dangerously-skip-permissions` to "turn off all permission checks so nothing can block." The right scope is the *minimum* set of tools the review needs — pre-authorized via `--allowedTools`, not switched off wholesale. For locked-down CI you can go further with a restrictive permission mode and `--bare` to skip auto-discovery of local config ([headless docs](https://code.claude.com/docs/en/headless)); the Agent SDK plugs the same call into a GitHub Actions workflow ([GitHub Actions](https://code.claude.com/docs/en/github-actions)).

```python
def claude_ci_command(prompt, allowed_tools, output_format="json"):
    return [
        "claude",
        "-p", prompt,                               # headless: never waits on a prompt
        "--allowedTools", ",".join(allowed_tools),  # scope EXACTLY what's needed
        "--output-format", output_format,           # parseable by the pipeline
    ]
```

### Routing jobs: synchronous vs. batch (4.5)

A CI pipeline runs more than one kind of Claude job, and they don't share a latency profile. A **blocking pre-merge check** gates a developer's merge — it must return now, so it's synchronous even at full price. An **overnight technical-debt report** is latency-tolerant — it belongs in the Batches API for the 50% saving and the up-to-24-hour window ([Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)). The deciding axis is simply whether something is *blocked waiting*:

```python
def route_review_job(job):
    return "sync" if job["blocking"] else "batch"
```

Batching the pre-merge check to save money is the trap from [6.2](../6.2-batch-processing/lesson.md): "done within 24 hours, no SLA" is unacceptable when a human is waiting.

### Reviewing the PR: independent, multi-pass (4.6)

The review itself uses the architecture from [6.3](../6.3-multi-instance-review/lesson.md). Each pass is an **independent instance** (a fresh context — none of the code's generation reasoning), because independent review catches what self-review misses ([Create custom subagents](https://code.claude.com/docs/en/sub-agents)). Concretely, each pass is a brand-new single-turn `client.messages.create` whose `messages` contain only the code and the review instruction — no assistant turns from generation threaded in; that fresh `messages` list *is* the independence. And a multi-file PR is split into **per-file passes plus one integration pass**, to avoid the attention dilution that makes a single giant pass thorough on some files and superficial — even contradictory — on others.

### Minimizing false positives: explicit criteria (4.1)

This is the scenario's stated objective — "minimize false positives" — and it's where developers either trust the bot or mute it. The fix isn't telling the model to "be conservative" (vague self-regulation drifts); it's **explicit categorical criteria**: name the issue types to report and the ones to skip. In the pipeline, the review tool returns a `category` per finding, and we keep only the in-scope categories. The stylistic nit the team does on purpose never reaches the PR:

```python
return [f for f in findings if f["category"] in report_categories]
```

Each finding also carries a `detected_pattern` (which construct triggered it) so that when developers *do* dismiss a finding, you can analyze which patterns are noisy and tighten them — the validation/feedback discipline from [6.1](../6.1-validation-retry-loops/lesson.md) applied to the reviewer itself.

## Worked example

The full pipeline: route the job, run the headless command for a blocking check, review with independent multi-pass review filtered to explicit criteria, and format actionable comments.

```python
def run_ci_review(client, pull_request):
    job = {"name": "pre-merge review", "blocking": True}
    where = route_review_job(job)                          # 4.5 -> "sync"

    # For a blocking check we invoke Claude Code headless in the pipeline step:
    cmd = claude_ci_command(                                # 3.6
        "Review the staged diff", allowed_tools=["Read", "Grep"],
    )

    # Independent, multi-pass review, filtered to the team's explicit criteria:
    findings = review_pull_request(                         # 4.6 + 4.1
        client, pull_request.files,
        report_categories={"security", "correctness", "performance"},
    )

    comments = format_pr_feedback(findings)                 # actionable output
    return {"ran_as": where, "command": cmd, "comments": comments}
```

`review_pull_request` does the per-file and integration passes and the category filter; `format_pr_feedback` turns each surviving finding into a `file:line [severity] issue` comment a developer can act on. The result is a review that runs without a human in the loop, costs the right amount per job, reads the PR carefully, and only speaks up about things the team actually cares about.

## Anti-patterns & pitfalls

This scenario's distractors are the union of the module's traps, in CI clothing:

1. **Running Claude Code interactively in CI.** The job hangs waiting on a permission prompt no one will answer. Run headless with `-p`. (Distractors invent `CLAUDE_HEADLESS=true` or `--batch`; those aren't real. The documented flag is `-p`.)
2. **Disabling all permission checks to stop the hang** (e.g. `--dangerously-skip-permissions`). Trading a hang for an unscoped agent in an automated pipeline. Pre-authorize the *minimum* tools with `--allowedTools`; never switch permissions off wholesale.
3. **Batching a blocking pre-merge check for the discount.** The 50% saving doesn't justify a 24-hour-window, no-SLA path for a check a developer is blocked on. Blocking → synchronous; only latency-tolerant jobs batch.
4. **Self-reviewing generated code, or one giant single-pass review.** Asking the generator to check its own work (it keeps its bias) or reviewing fourteen files in one prompt (attention dilution). Use an independent instance and split into per-file + integration passes.
5. **Posting every finding / telling the model to "be conservative."** Both keep the noise. Vague "be conservative" doesn't define the boundary; posting everything pushes triage onto developers and erodes trust. Define **explicit categorical criteria** — report these types, skip those — and filter to them.

The throughline: a trustworthy CI reviewer is **headless, correctly scoped, routed by latency, independent and multi-pass, and filtered to explicit criteria**. Drop any one and you get the failure that scenario question is built around.

## Exam focus

Scenario 5 questions are *applied* — they wrap a single task statement in the CI narrative and offer the module's anti-patterns as distractors. The headless question's answer is `-p` (not invented env vars/flags, not "disable permissions"). The cost question keeps the blocking check synchronous and batches only the overnight job. The large-PR question splits into per-file + integration passes (not a bigger model, not mandating smaller PRs). The false-positive question reaches for explicit categorical criteria (not "be conservative," not posting everything with a "low confidence" prefix). Recognize which task statement a scenario question is really testing, and the correct answer is the prescribed approach from that chapter.

## References & further reading

- [Run Claude Code programmatically (headless)](https://code.claude.com/docs/en/headless) — `claude -p` non-interactive mode, `--allowedTools`, `--output-format json`, and `--bare` for reproducible CI runs.
- [GitHub Actions](https://code.claude.com/docs/en/github-actions) — wiring the Agent SDK / Claude Code into a CI workflow.
- [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) — the 50% / 24-hour-window trade that decides which CI jobs batch.
- [Create custom subagents](https://code.claude.com/docs/en/sub-agents) — independent reviewer instances, each in their own context window.

## Exam coverage

- **CCAF** — Exam Scenario 5: Claude Code for Continuous Integration. This capstone's authoritative mapping is **Scenario 5**. It *integrates* — as applied context — Domain 3 Task Statement 3.6 (Integrate Claude Code into CI/CD pipelines) and Domain 4 Task Statements 4.1 (explicit criteria to reduce false positives), 4.4 (validation), 4.5 (batch processing), and 4.6 (multi-instance/multi-pass review). Those task statements have their own dedicated chapters (3.6 → 5.7; 4.1 → 1.1; 4.4–4.6 → 6.1–6.3); this chapter applies them together, it isn't their canonical home.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
