Grade the user's Learn Claude exercise against the lesson rubric.

The user invoked `/verify $ARGUMENTS`. Treat `$ARGUMENTS` as a lesson ID in dotted form (`module.lesson`, e.g. `3.1`). If empty, ask which lesson and stop.

> **Phase 2:** grading is now done by the dedicated `verifier` subagent (backed by the grading MCP server, with a Bash fallback) — you no longer grade inline. Your job here is to dispatch to it, persist its report, and suggest a next step.

## Steps

1. **Sanity-check the chapter exists.** Use Glob to confirm `lessons/**/$ARGUMENTS-*/rubric.yaml` exists. If missing, stop and tell the user the lesson isn't built yet (point them at `docs/curriculum-map.md`).

2. **Delegate grading to the `verifier` subagent.** Spawn the `verifier` subagent (via the Agent tool, `subagent_type: verifier`) with the chapter id `$ARGUMENTS` as its input. It will:
   - load the rubric (`lessons/**/$ARGUMENTS-*/rubric.yaml`),
   - confirm the learner's work exists at `~/learn-claude-work/$ARGUMENTS/` (if not, it tells the user to run `/exercise $ARGUMENTS`),
   - dispatch each criterion on its `check` (`bash_execution` → run its `command` in the work dir; `code_review` / `anti_pattern` → read the source),
   - and return a weighted `N/100` Markdown report.

   Do **not** re-grade or second-guess the verifier — its returned report is authoritative. Take its Markdown report verbatim as the result.

3. **Show the report to the user.** Print the verifier's report to chat as-is.

4. **Log the report to disk.** Persist the same report so the user has a history of attempts:

   ```bash
   mkdir -p ~/learn-claude-work/$ARGUMENTS/results
   ```

   Then use the Write tool to create `~/learn-claude-work/$ARGUMENTS/results/<UTC-timestamp>.md`, where the timestamp is ISO-8601 with `:` replaced by `-` for filesystem-safety (e.g. `2026-05-28T14-32-07Z.md`). Get the timestamp with `date -u +%Y-%m-%dT%H-%M-%SZ`. The file's content is the verifier's full report. Mention the path in your reply so the user can find it.

   The `results/` directory lives in the user's home tree, outside the repo, so it never gets committed.

5. **Record the score (optional, non-blocking).** So the Phase-4 `/coach` can track mastery, record the verifier's score for this chapter. Read the numeric `N` out of the report's `N/100` total (an integer 0–100). If the progress MCP server is registered this session, call its `mcp__learn-claude-progress__record_verify` tool with `chapter: $ARGUMENTS` and `score: <N>`. If it isn't available, fall back to Bash: `python3 infra/progress-mcp/progress.py verify $ARGUMENTS <N>`. **Ignore any failure silently** — tracking must never change or block the grade. The score recorded is the verifier's, exactly as reported.

6. **Suggest a next step.** If they passed (≥80), congratulate them and point at the next lesson in `docs/curriculum-map.md`. If they failed, point them at the report's Fixes section and suggest re-reading the relevant part of `lesson.md` before iterating with `/verify $ARGUMENTS` again.

## Tone

Be a fair messenger. The verifier is the unforgiving grader; you relay its verdict honestly and make the next step obvious. Don't soften a fail, and don't inflate a pass — the score is the verifier's, not yours.
