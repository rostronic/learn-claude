Set up the hands-on exercise for a Learn Claude lesson.

The user invoked `/exercise $ARGUMENTS`. Treat `$ARGUMENTS` as a lesson ID in dotted form (`1.1`, `2.3`, etc.). If empty, ask which lesson and stop.

## Steps

1. **Find the exercise.** Use Glob to locate `lessons/**/$ARGUMENTS-*/exercise.md` and the sibling `starter/` directory. If either is missing, tell the user the exercise isn't built yet (point them at `docs/curriculum-map.md`) and stop.

2. **Copy the starter to the user's work directory.** Use Bash:
   ```bash
   mkdir -p ~/learn-claude-work/$ARGUMENTS
   cp -R lessons/**/$ARGUMENTS-*/starter/. ~/learn-claude-work/$ARGUMENTS/
   ```
   The `cp -R ... /. ...` form copies directory contents (including dotfiles) without re-nesting. Do NOT modify the repo's `starter/` — that's the pristine template. If `~/learn-claude-work/$ARGUMENTS/` already exists and has content, ask the user before overwriting (they may have in-progress work).

3. **Read the exercise instructions to the user.** Use the Read tool on `exercise.md`. Then walk through it in your own words — what they're building, the function signature they need to implement, the constraints (especially the MUST NOT items, which mirror the rubric's `anti_pattern` checks), and how to run the tests.

4. **Tell them where the code lives and what to do next:**
   - "Your work directory is `~/learn-claude-work/$ARGUMENTS/`. Edit the files there — the repo's `starter/` stays clean so you can reset."
   - "Install deps with `pip install -r ~/learn-claude-work/$ARGUMENTS/requirements.txt` (use a venv if you like)."
   - "Run tests with `cd ~/learn-claude-work/$ARGUMENTS && pytest`."
   - "When your tests pass — or when you're stuck — run `/verify $ARGUMENTS` and I'll grade you against the rubric."

## Tone

Set them up to start coding fast. Don't lecture; the lesson already did that. If they ask a clarifying question about the exercise, answer it without giving away the implementation — the point is for them to write the code.
