Drill the user with a practice question for one chapter, hiding the answer until they commit.

The user invoked `/practice $ARGUMENTS`. Treat `$ARGUMENTS` as a chapter id in dotted form (`module.lesson`, e.g. `3.1`) — the same course-order id `/study`, `/exercise`, and `/verify` use. If empty, ask which chapter and stop.

> Questions are administered by the dedicated `examiner` subagent. The point of going through it: the examiner reads `practice.yaml` (which contains the answer key) **so this conversation never does** — you stay blind to the correct letter while the user answers, which is what makes the quiz honest. Don't read `practice.yaml` yourself.

## Steps

1. **Find the practice file.** Use Glob for `lessons/**/$ARGUMENTS-*/practice.yaml`. If nothing matches, tell the user there's no practice bank for that chapter yet (some built chapters may not have one), point them at `/study $ARGUMENTS` to review or `docs/curriculum-map.md` for what's built, and stop. Do **not** open the file.

2. **Get a question from the examiner (PRESENT mode).** Spawn the `examiner` subagent (Agent tool, `subagent_type: examiner`) with a PRESENT-mode request: pass the `practice.yaml` path, ask for **one `random` question**, and include a seed token so repeat runs vary (get one with `date -u +%s` via Bash, or reuse any varying token). The examiner returns *only* the `QUESTION <id>` block — stem + A/B/C/D, **no answer**. That's deliberate: the key is not in your context.

3. **Present it and wait.** Show the user the examiner's question block verbatim and ask them to pick A, B, C, or D. **Stop and wait for their answer.** Do not speculate about which option is right, do not "think out loud" toward an answer — you genuinely don't have the key, and pretending to reason toward it would undercut the drill. (If the user asks you to just tell them the answer, decline and tell them to commit to a letter first — that's the whole point.)

4. **Reveal via the examiner (GRADE mode).** Once the user answers, spawn the `examiner` again in GRADE mode: pass the same `practice.yaml` path and the single `{id, answer}` pair (the `id` from step 2, the user's letter). It returns the `RESULT` block — whether they were right, the correct option, and the explanation of why each distractor fails. Show it verbatim.

5. **Record the attempt (optional, non-blocking).** The examiner's `RESULT` block tells you whether the user got it right — record that for the Phase-4 `/coach`. If the progress MCP server is registered this session, call its `mcp__learn-claude-progress__record_practice` tool with `chapter: $ARGUMENTS` and `correct: <true|false>` (true iff the RESULT marked them correct). If it isn't available, fall back to Bash: `python3 infra/progress-mcp/progress.py practice $ARGUMENTS <true|false>`. **Ignore any failure silently.** Note you're only recording the user's *own* committed answer here — this stays consistent with never holding the key before they answer.

6. **Offer the next step.** After the reveal, offer another question (`/practice $ARGUMENTS` again), or — if they're ready to build — point at `/verify $ARGUMENTS` to be graded on the exercise, or the next chapter in `docs/curriculum-map.md`. One or two lines, conversational.

## Tone

You're a quizmaster, not a tutor mid-question. Be brief and a little sporting while the question is open — you're holding the card, not reading it. Save the teaching for the reveal, where the examiner's explanation does the heavy lifting; add a sentence of encouragement or a pointer to the relevant part of `lesson.md` if they missed it, but don't relitigate the rationale. Never reveal or hint at the answer before they've committed.
