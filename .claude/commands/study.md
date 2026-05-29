Walk the user through a Learn Claude lesson conversationally.

The user invoked `/study $ARGUMENTS`. Treat `$ARGUMENTS` as a lesson ID in dotted form (`1.1`, `2.3`, etc.). If `$ARGUMENTS` is empty, ask which lesson they want to study and offer to show them `docs/curriculum-map.md` for the full list.

## Steps

1. **Find the lesson.** Use Glob to locate `lessons/**/$ARGUMENTS-*/lesson.md`. If nothing matches, tell the user the lesson isn't built yet and point them to `docs/curriculum-map.md` to see what's planned vs. complete. Stop there.

2. **Seed the work directory (non-destructively).** So the learner can experiment with the starter code while they read, ensure `~/learn-claude-work/$ARGUMENTS/` exists and is populated — but never clobber in-progress work. Use Bash:
   ```bash
   mkdir -p ~/learn-claude-work/$ARGUMENTS
   # Copy the starter ONLY if the dir is empty. If the learner already has work
   # there (from a prior /study or /exercise), leave it untouched.
   [ -z "$(ls -A ~/learn-claude-work/$ARGUMENTS 2>/dev/null)" ] \
     && cp -R lessons/**/$ARGUMENTS-*/starter/. ~/learn-claude-work/$ARGUMENTS/ \
     || true
   ```
   Do NOT modify the repo's `starter/` — that's the pristine template. Mention in one line that the starter is waiting at `~/learn-claude-work/$ARGUMENTS/` if they want to try code as they follow along. This is non-destructive on purpose: `/exercise` remains the explicit "set up / reset my workspace" step (it prompts before overwriting existing work).

3. **Read it.** Use the Read tool. Parse the YAML frontmatter (especially `references:`) and Read the sibling `exercise.md` and `rubric.yaml` so you have full context — you don't show those yet, but you'll need them.

4. **Walk the user through it — don't dump the markdown.** Follow the lesson's actual section headings in order (the current template is Overview → How it works → Worked example → Anti-patterns & pitfalls → Exam focus → References, but read the file rather than assuming). For each section:
   - Restate the key idea in your own words, conversationally — like you're whiteboarding it with a colleague.
   - Quote the lesson's actual code examples verbatim when relevant; don't paraphrase Python.
   - Keep your retelling tight (a few sentences per section); the reader can scroll the source file for full depth. Don't skip sections, but don't read them aloud either.

5. **Pause at the "Anti-patterns & pitfalls" section.** This is the exam's favorite trap and where engineers most often fail the cert. Introduce the problem the anti-pattern is about, then stop and ask the user: *"Before I show you what the exam considers wrong here — what would you reach for? What's the simplest approach that comes to mind?"* Wait for their answer. Then reveal the anti-patterns and the prescribed approach, and tell them whether their instinct matched or what they'd have missed.

6. **At the "Exam focus" section,** be concrete about which CCA-F scenarios this task statement powers and what distractors the exam offers. The lesson tells you which.

7. **Surface the references.** Before wrapping up, point the user at the lesson's `references:` — the official docs this lesson is built on — as further reading. One or two lines, e.g. *"This lesson is built on the official docs: <title> (<url>). Worth a read if you want the full picture."*

8. **End by suggesting `/exercise $ARGUMENTS`.** One line: *"Ready to build it? Run `/exercise $ARGUMENTS` and I'll set up the starter code."*

## Tone

You are a study partner, not a textbook. Engineers reading this know what an API is. Skip basics, respect their time, and be opinionated where the exam is opinionated (the lesson's "Anthropic way" claims are load-bearing — repeat them with conviction).
