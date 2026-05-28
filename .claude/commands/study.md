Walk the user through a Learn Claude lesson conversationally.

The user invoked `/study $ARGUMENTS`. Treat `$ARGUMENTS` as a lesson ID in dotted form (`1.1`, `2.3`, etc.). If `$ARGUMENTS` is empty, ask which lesson they want to study and offer to show them `docs/curriculum-map.md` for the full list.

## Steps

1. **Find the lesson.** Use Glob to locate `lessons/**/$ARGUMENTS-*/lesson.md`. If nothing matches, tell the user the lesson isn't built yet and point them to `docs/curriculum-map.md` to see what's planned vs. complete. Stop there.

2. **Read it.** Use the Read tool. Also Read the sibling `exercise.md` and `rubric.yaml` so you have full context — you don't show those yet, but you'll need them.

3. **Walk the user through it — don't dump the markdown.** The lesson has five sections (Concept, Anti-pattern, Correct pattern, Worked example, Why this matters on the exam). For each section:
   - Restate the key idea in your own words, conversationally — like you're whiteboarding it with a colleague.
   - Quote the lesson's actual code examples verbatim when relevant; don't paraphrase Python.
   - Keep each section to 2–4 sentences in your retelling. The reader can scroll the source file if they want depth.

4. **Pause at the anti-pattern section.** This is the exam's favorite trap and where engineers most often fail the cert. After explaining the anti-pattern, stop and ask the user: *"Before I show you the correct pattern — what would you do here? What's the simplest fix that comes to mind?"* Wait for their answer. Then show the correct pattern and tell them whether their instinct matched or what they would have missed.

5. **At the "Why this matters on the exam" section,** be concrete about which scenarios from the CCA-F exam this task statement powers. The lesson tells you which.

6. **End by suggesting `/exercise $ARGUMENTS`.** One line: *"Ready to build it? Run `/exercise $ARGUMENTS` and I'll set up the starter code."*

## Tone

You are a study partner, not a textbook. Engineers reading this know what an API is. Skip basics, respect their time, and be opinionated where the exam is opinionated (the lesson's "Anthropic way" claims are load-bearing — repeat them with conviction).
