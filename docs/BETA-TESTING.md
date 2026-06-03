# Beta testing Learn Claude

Thanks for taking this for a spin — you're doing me a real favor. This guide gets you from a fresh clone to running the whole platform in a few minutes, then points you at the kinds of feedback that help most.

You don't need to be studying for the exam to test this. If you can read a lesson and notice when something is confusing, wrong, or won't run, you're exactly the tester I need.

## Setup (one time)

**Prerequisites**

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and authenticated.
- Python 3.10+ with `pip`.
- (Optional) `ANTHROPIC_API_KEY` exported in your shell — only needed if you actually run an exercise's tests against the real API. The platform itself never calls the API.

**Install the two MCP servers' dependencies**

```bash
pip install -r infra/grading-mcp/requirements.txt
pip install -r infra/progress-mcp/requirements.txt
```

**Approve the MCP servers**

The repo ships a project [`.mcp.json`](../.mcp.json) that registers two servers: `learn-claude-grading` (used by `/verify`) and `learn-claude-progress` (used by `/coach`). When you open the repo in Claude Code, it will prompt you to approve them — say yes to both. If you decline, things still work: `/verify` falls back to running checks directly, and `/coach` falls back to reading progress from disk.

```bash
claude   # open Claude Code in the repo, approve both servers when prompted
```

That's it. Your work and progress are written to `~/learn-claude-work/` — **outside the repo**, so nothing you do dirties the clone.

## The happy path to try

Run these in order. The whole loop should take 20–30 minutes and exercises every part of the platform.

1. **`/study 0.1`** — the true start of the learning path (Foundations: the four technologies). Read it like a real lesson and see if it lands.
2. **`/study 3.1`** — Agentic loops. This is the canonical "first real chapter" to test the study experience on.
3. **`/exercise 3.1`** — copies the starter into `~/learn-claude-work/3.1/` for you to edit.
4. **Implement it** — open `~/learn-claude-work/3.1/`, follow the exercise instructions, and write the code.
5. **`/verify 3.1`** — grades your work against the rubric (through the grading MCP server) and writes a report to `~/learn-claude-work/3.1/results/`.
6. **`/practice 3.1`** — one multiple-choice question for the chapter; the answer stays hidden until you commit, then it explains the rationale.
7. **`/mock-exam CCAF`** — a full, timed, domain-weighted mock exam (scaled score out of 1000, pass 720). It draws a random subset of scenarios each run.
8. **`/coach CCAF`** — reads your history and hands back a prioritized "do this next" plan.

**A note on the capstones (7.7–7.10).** These four — plus 5.8 and 6.4 — are the CCAF exam scenarios and are **design exercises**, not coding ones. For those, `/exercise` asks you to write a `design.md` (an architecture/approach writeup), not Python. If you test one, the absence of code and tests is expected — verify grades the design instead.

## What feedback helps most

I care less about typos (though flag them if you like) and more about anything that breaks trust in the content or the tooling. Specifically:

- **Confusing explanations** — a lesson section you had to re-read, an analogy that didn't click, a leap that lost you.
- **Wrong or ambiguous answer keys** — a practice/mock-exam question where the "correct" answer seems wrong, or more than one option looks right.
- **Broken exercises or tests** — a starter that won't run, a test that fails before you've touched it, instructions that don't match the code.
- **Citations that don't support the claim** — a lesson links an official doc, you click it, and it doesn't actually back what the lesson said.
- **Anything that doesn't run** — a command that errors, a server that won't start, a `pip install` that fails.

## How to report it

Open a GitHub issue — there are two forms that make this quick:

- **[Lesson feedback](https://github.com/rostronic/learn-claude/issues/new?template=lesson-feedback.yml)** — for anything about a specific chapter's content: confusing, inaccurate, broken exercise, or a wrong answer key.
- **[Bug report](https://github.com/rostronic/learn-claude/issues/new?template=bug-report.yml)** — for a command or platform problem: something errored, didn't run, or behaved unexpectedly.

(Both links also live under **New Issue → Choose a template** in the GitHub UI.)

When in doubt, just open an issue and pick whichever form is closer — I'd rather get a slightly-miscategorized report than no report. Thank you!
