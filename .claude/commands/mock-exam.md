Administer a full, timed, domain-weighted mock exam and score it on the scaled scale.

The user invoked `/mock-exam $ARGUMENTS`. Treat `$ARGUMENTS` as an **exam code** (e.g. `CCAF`) — like `/exam`, this command's argument is an exam code, not a `module.lesson` chapter id. If empty or unrecognized, list the available exams (the subdirectories of `exams/`) and stop.

> The `examiner` subagent administers and scores the exam. As with `/practice`, the reason to route through it is **context isolation**: the examiner reads the question bank (with its answer key) so this conversation never holds the key while the user is answering. You assemble nothing and grade nothing yourself — you administer the set the examiner hands back, collect answers, and hand them back for scoring.

## Steps

1. **Resolve the exam.** Use Glob/Bash to confirm `exams/$ARGUMENTS/exam.yaml` exists. If `exams/` has no such subdirectory, list the available exam codes (`ls exams/`) and stop — don't guess. Do **not** open the question files yourself.

2. **Assemble the set (examiner ASSEMBLE mode).** Spawn the `examiner` subagent (Agent tool, `subagent_type: examiner`) in ASSEMBLE mode: pass the `exams/$ARGUMENTS/` path and a seed token (get one with `date -u +%s`). The examiner reads `exam.yaml` for config (`passing_score` 720, `scaled_max` 1000, `scenario_count` 4, `target_questions` ~30, domain weights), **picks 4 of the 6 scenarios at random**, and assembles ~30 **domain-weighted** questions (CCA-F weights: D1 27, D2 18, D3 20, D4 20, D5 15). It returns a `PLAN` (scenarios chosen, per-domain counts, any shortfalls) and the `SET` — stems + options only, **no answers**.

3. **Brief the user and start the soft timer.** Show the PLAN so they know the shape of the exam (how many questions, which scenarios, the domain spread). Tell them this is a **soft, advisory timer** — note the start time (`date -u`) and a suggested budget (the real CCA-F gives ~90 minutes for ~60 questions, so ~45 min for a ~30-question half-length run is a fair pace). It will *not* cut them off; it's there so they can practice pacing. Then administer the set.

4. **Administer the set, one question at a time.** Walk the `SET` in order. For each: show the question number, the stem, and A/B/C/D, and wait for the user's letter before moving on. Keep a running list of `{id, answer}` as you go. Be efficient — this is a 30-question run; don't editorialize between questions, and **never reveal or hint at any answer** (you don't have the key, and the reveal is the examiner's job at the end). If the user wants to skip a question, record it as unanswered and move on. Periodically (e.g. every ~10 questions, or if they ask) you may note elapsed time against the advisory budget.

5. **Score it (examiner GRADE mode).** When the last question is answered, spawn the `examiner` again in GRADE mode: pass the `exams/$ARGUMENTS/` path and the full list of `{id, answer}` pairs. It returns the `MOCK RESULT` — a scaled `N/1000` score (`scaled = round(1000 × domain-weighted fraction correct)`, an approximation of Anthropic's scaled model), PASS/FAIL against 720, a per-domain breakdown, and the missed questions with explanations and their task statements. Show this report to the user.

6. **Add review pointers.** Translate the weak domains/task statements into concrete next steps using `docs/exam-mapping.md`. Read its `exams: $ARGUMENTS` coverage list and, for each weak domain (and each missed question's `task_statement`), name the **course chapter** that covers it (`lesson_chapter`) and whether it's `built` (studyable now via `/study <chapter>` / `/practice <chapter>`) or `planned`. Present this as a short "what to review" list — domain → task statements → chapters. This is the bridge from a score to a study plan.

7. **Persist the result outside the repo.** Save the full report so the user keeps a history — in their home tree, **never in the repo** (it's user data and must never be committed):

   ```bash
   mkdir -p ~/learn-claude-work/mock-exams/$ARGUMENTS
   ```

   Then use the Write tool to create `~/learn-claude-work/mock-exams/$ARGUMENTS/<UTC-timestamp>.md`, where the timestamp is ISO-8601 with `:` replaced by `-` (get it with `date -u +%Y-%m-%dT%H-%M-%SZ`, e.g. `2026-05-29T23-04-11Z.md`). The file content: the examiner's `MOCK RESULT` report, the PLAN (which scenarios/questions were drawn), the elapsed time vs. the advisory budget, and your review pointers. Mention the path in your reply.

8. **Suggest a next step.** If they passed (≥720), congratulate them and suggest a fresh run (selection re-randomizes) or drilling any still-weak domain with `/practice <chapter>`. If they didn't, point them at the weakest domain's chapters from step 6 — study/practice those, then re-run `/mock-exam $ARGUMENTS`.

## Tone

You're a proctor, then a coach. During the exam: crisp, neutral, no tells, keep them moving. After: hand them the examiner's verdict straight (don't inflate or soften the scaled score — it's the examiner's, not yours), then turn the weak spots into a concrete route back into the course. Always be explicit that the scaled score is an approximation of Anthropic's model, not the official algorithm.
