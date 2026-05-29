Turn the exam-agnostic learning path into an exam-specific course, walking its chapters in the exam's own order.

The user invoked `/exam $ARGUMENTS`. Treat `$ARGUMENTS` as an **exam code** (e.g. `CCAF`), optionally followed by a refinement: a domain filter (`CCAF domain 1`, `CCAF 2`), or `resume`/`continue`. This is the one command in the repo whose argument is an *exam code*, not a `module.lesson` chapter id — exams are an overlay on the course, and this command is the overlay's entry point.

The single source of truth is [`docs/exam-mapping.md`](../../docs/exam-mapping.md). Read its YAML frontmatter — never hard-code the mapping, and never reorder or renumber chapters. Lessons stay exam-agnostic; you are only *presenting* them in a chosen exam's order.

## Steps

1. **Read the mapping.** Read `docs/exam-mapping.md` and parse the `exams:` frontmatter. Each key under `exams:` is an exam code with `title`, `guide_url`, and an ordered `coverage:` list of `{ task_statement, domain, lesson_chapter, lesson_slug?, status }` — already in that exam's own order. Don't re-sort it; the file order *is* the exam order.

2. **Resolve the exam code.** Match `$ARGUMENTS` (the leading token) against the `exams:` keys, case-insensitively.
   - **Empty argument:** list the available exams — for each, its code, `title`, and how many task statements are built vs. total (count `status: built` over the `coverage:` length). Ask which one they want and suggest `/exam <CODE>`. Stop.
   - **No match:** tell the user that code isn't mapped, list the available codes (as above), and stop. Don't guess.

3. **Present the exam in exam order — conversationally, not as a file dump.** Once resolved, give a short orientation: the exam's full title, a one-line pointer to its official guide (`guide_url`), and the built-vs-total count. Then walk the `coverage:` list **in file order**, grouped by `domain` (Domain 1 → 5, then the `scenario` group), as a compact checklist. For each task statement show:
   - the task-statement id + title,
   - the course **chapter** that covers it (`lesson_chapter`),
   - a built/planned marker (e.g. ✅ built / ◻️ planned).

   Keep it scannable — this is a map, not a recitation. The point the learner should take away: the chapters are *not* in numeric order here (e.g. CCAF opens on chapter 3.1, and its Domain 4 reaches back to 1.1) — that's expected, because the course is dependency-ordered while the exam has its own spine.

4. **Honor a domain filter if given.** If `$ARGUMENTS` named a domain (`domain 1`, `2`, `scenario`), present only that domain's slice of `coverage:` (still in file order) and offer to walk it.

5. **Offer the guided walkthrough.** Built chapters can be studied right now; planned ones can't. Offer to walk the user through the **built** chapters **in exam order**, one at a time, by reusing the `/study` flow per chapter:
   - For each `coverage:` entry in order, locate the lesson with Glob: `lessons/**/<lesson_chapter>-*/lesson.md`.
   - If it's **built** (lesson found), study it by following the `/study` walkthrough for that chapter — same conversational treatment, the Anti-patterns pause, references, all of it. (Don't re-dump; *use* the lesson.) Treat `<lesson_chapter>` exactly as `/study`'s `$ARGUMENTS`.
   - If it's **planned** (no lesson, or `status: planned`), announce it in one line ("Next on the CCAF path is *<task statement>* → chapter <n>, not built yet — skipping") and move to the next built chapter. Never block the walkthrough on a planned chapter.
   - Between chapters, check in rather than steamrolling — confirm they want to continue to the next one.

6. **Support resume / pick.** If `$ARGUMENTS` included `resume`/`continue`, or the user asks to jump around, let them. There's no persisted progress store in Phase 1, so ask where they left off (or which task statement / chapter to start from) and begin the walkthrough there. Offer the first **built** chapter as the default starting point.

7. **End by pointing at the next built chapter in exam order.** Close with the concrete next step — the earliest built chapter they haven't done yet, e.g. *"Start the CCAF path with `/study 3.1` (Agentic loops), or say 'walk me through it' and I'll take you chapter by chapter."* If every built chapter is done, say so and note that the remaining task statements are planned (point at [`docs/curriculum-map.md`](../../docs/curriculum-map.md) for the build-out roadmap).

## Tone

You're a study guide turning a syllabus into a route. Be opinionated and orienting: make clear *why* the order looks scrambled against the chapter numbers (dependency-ordered course vs. exam spine), and keep the learner moving toward the next thing they can actually study. Don't lecture the lesson content here — that's `/study`'s job; this command routes, `/study` teaches.
