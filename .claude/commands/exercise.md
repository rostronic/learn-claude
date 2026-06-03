Set up the hands-on exercise for a Learn Claude lesson.

The user invoked `/exercise $ARGUMENTS`. Treat `$ARGUMENTS` as a lesson ID in dotted form (`1.1`, `2.3`, etc.). If empty, ask which lesson and stop.

## Steps

1. **Find the exercise.** Use Glob to locate `lessons/**/$ARGUMENTS-*/exercise.md`. If it's missing, tell the user the exercise isn't built yet (point them at `docs/curriculum-map.md`) and stop. Then check whether a sibling `starter/` directory exists — that determines which kind of exercise this is:
   - **`starter/` exists → a coding exercise** (most chapters). Follow step 2a.
   - **No `starter/` → a design exercise** (the scenario capstones, e.g. 7.7–7.10, where the deliverable is a written `design.md`, not code). Follow step 2b. Do NOT tell the user it "isn't built" — a missing starter is expected here.

2a. **Coding exercise — copy the starter to the user's work directory.** Use Bash:
   ```bash
   mkdir -p ~/learn-claude-work/$ARGUMENTS
   cp -R lessons/**/$ARGUMENTS-*/starter/. ~/learn-claude-work/$ARGUMENTS/
   ```
   The `cp -R ... /. ...` form copies directory contents (including dotfiles) without re-nesting. Do NOT modify the repo's `starter/` — that's the pristine template. If `~/learn-claude-work/$ARGUMENTS/` already exists and has content, ask the user before overwriting (they may have in-progress work).

2b. **Design exercise — just create the work directory** (there's no starter to copy):
   ```bash
   mkdir -p ~/learn-claude-work/$ARGUMENTS
   ```
   The deliverable is a document the learner writes themselves (`exercise.md` names it, usually `design.md`). Don't reference `pip install`/`pytest` for these — there's nothing to run; the verifier grades the written design against the rubric's `code_review`/`anti_pattern` criteria.

3. **Read the exercise instructions to the user.** Use the Read tool on `exercise.md`. Then walk through it in your own words — for a coding exercise: what they're building, the function signature, the constraints (especially the MUST NOT items, which mirror the rubric's `anti_pattern` checks), and how to run the tests. For a design exercise: the sections their `design.md` must cover and the anti-patterns the scenario tempts them with.

4. **Tell them where the work lives and what to do next:**
   - "Your work directory is `~/learn-claude-work/$ARGUMENTS/`."
   - **Coding exercise:** "Edit the starter files there (the repo's `starter/` stays clean so you can reset). Install deps with `pip install -r ~/learn-claude-work/$ARGUMENTS/requirements.txt`, run tests with `cd ~/learn-claude-work/$ARGUMENTS && pytest`."
   - **Design exercise:** "Write your `design.md` there covering the sections from `exercise.md`."
   - "When you're ready — or stuck — run `/verify $ARGUMENTS` and I'll grade you against the rubric."

## Tone

Set them up to start coding fast. Don't lecture; the lesson already did that. If they ask a clarifying question about the exercise, answer it without giving away the implementation — the point is for them to write the code.
