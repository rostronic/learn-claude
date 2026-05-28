Grade the user's Learn Claude exercise against the lesson rubric.

The user invoked `/verify $ARGUMENTS`. Treat `$ARGUMENTS` as a lesson ID in dotted form. If empty, ask which lesson and stop.

> **Phase 1 note:** Verification in Phase 1 is manual — you (Claude) read the rubric and the user's code and make the call. This is inconsistent across sessions, which is exactly why Phase 2 replaces it with a dedicated `verifier` subagent backed by a grading MCP server. Mention this at the end of your report so the user knows the score has a margin of error.

## Steps

1. **Find the rubric and user's work.**
   - Use Glob to locate `lessons/**/$ARGUMENTS-*/rubric.yaml`. If missing, stop and tell the user the lesson isn't built yet.
   - Check that `~/learn-claude-work/$ARGUMENTS/` exists. If not, tell the user to run `/exercise $ARGUMENTS` first and stop.

2. **Read the rubric.** Use Read on the `rubric.yaml`. Note the `task_statement`, the list of criteria, and for each: `id`, `description`, `weight`, `check`, and (if present) `command`.

3. **Read the user's work.** Use Read on every code file in `~/learn-claude-work/$ARGUMENTS/`. You need full source visibility to grade `code_review` and `anti_pattern` criteria.

4. **Run tests once, up front.** Use Bash:
   ```bash
   cd ~/learn-claude-work/$ARGUMENTS && pytest -v
   ```
   Capture full output — you'll cite it for any `bash_execution` criterion whose `command` matches a pytest invocation. If `pytest` isn't installed, tell the user to `pip install -r requirements.txt` first.

5. **Grade each criterion.** Walk the rubric in order. For each:
   - **`code_review`** — read the user's source and decide whether the assertion in `description` holds. Pass/fail + one sentence of rationale citing the specific line or function.
   - **`anti_pattern`** — read the user's source looking for the forbidden pattern. Fail if present. Pass otherwise. One sentence of rationale, naming the pattern.
   - **`bash_execution`** — pass iff the criterion's `command` exited 0 in step 4. If it's a pytest command and some tests failed, fail this criterion and cite which tests.

6. **Calculate the weighted score.** Sum the `weight` of every passing criterion. Report as `N/100`.

7. **Report.** Format:

   ```
   Lesson $ARGUMENTS — <task statement title>
   Score: N/100

   ✓ <criterion id> (weight) — <one-sentence rationale>
   ✗ <criterion id> (weight) — <one-sentence rationale>
   ...

   Phase 1 note: this score is from manual grading. Phase 2 will replace `/verify`
   with a verifier subagent for consistency. Re-run after fixing failures.
   ```

   For failed criteria, point the user at the specific file and line where the fix needs to land — don't just restate the rubric.

8. **Log the report to disk.** Persist the same report you printed to chat so the user has a history of attempts:

   ```bash
   mkdir -p ~/learn-claude-work/$ARGUMENTS/results
   ```

   Then use the Write tool to create `~/learn-claude-work/$ARGUMENTS/results/<UTC-timestamp>.md`, where the timestamp is ISO-8601 with `:` replaced by `-` for filesystem-safety (e.g. `2026-05-28T14-32-07Z.md`). The file's content is the full report from step 7. Mention the path in your reply so the user can find it.

   The `results/` directory lives in the user's home tree, outside the repo, so it never gets committed.

9. **Suggest a next step.** If they passed (≥80, say), congratulate them and point at the next lesson in `docs/curriculum-map.md`. If they failed, suggest re-reading the relevant section of `lesson.md` and iterating.

## Tone

Be a fair grader. The exam itself is unforgiving — the rubric reflects that. Don't give partial credit on `anti_pattern` criteria (it's binary: present or not present). Don't sugarcoat a fail. But also: cite *why* in a way the user can act on.
