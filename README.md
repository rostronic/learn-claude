# Learn Claude

An open-source, Claude Code-native study platform for the **Claude Certified Architect — Foundations (CCA-F)** certification exam. Clone the repo, open Claude Code, type `/study 1.1`, and start working through lessons that map 1:1 to the official CCA-F task statements. Each lesson ends in a hands-on coding exercise, graded against a rubric drawn straight from the exam guide.

## Quick start

```bash
git clone <this-repo> learn-claude
cd learn-claude
claude                 # open Claude Code in this directory
/study 1.1             # walks you through Lesson 1.1 — Agentic Loops
/exercise 1.1          # copies the starter to ~/learn-claude-work/1.1/
/verify 1.1            # grades your work against the rubric, results in ~/learn-claude-work/1.1/results
```

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and authenticated
- `ANTHROPIC_API_KEY` exported in your shell (only needed to run exercise tests against the real API; the platform itself doesn't call the API)
- Python 3.10+ with `pip` (exercises use `pip install -r requirements.txt && pytest`)

## Status

**Phase 1 of 5.** One lesson is fully built (1.1 — Agentic Loops) as the template. The remaining 36 lessons are scaffolded in [docs/curriculum-map.md](docs/curriculum-map.md) and will be built out in subsequent phases:

- **Phase 1** (current) — Skeleton repo, slash commands, one lesson end-to-end
- **Phase 2** — Verifier subagent + grading MCP server (automated rubric checks)
- **Phase 3** — Examiner subagent, question bank, `/practice` and `/mock-exam`
- **Phase 4** — Coach subagent (hub-and-spoke coordinator) + progress tracking
- **Phase 5** — Authoring commands (`/new-lesson`, `/new-question`) + full content build-out

## Disclaimer

Unofficial. Not affiliated with, endorsed by, or sponsored by Anthropic. Built as exam-prep using the public [Claude Certified Architect — Foundations Certification Exam Guide](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F8lsy243ftffjjy1cx9lm3o2bw%2Fpublic%2F1773274827%2FClaude+Certified+Architect+%E2%80%93+Foundations+Certification+Exam+Guide.pdf) as the source of truth.

## License

MIT. See [LICENSE](LICENSE) (to be added).

## Contributing

The platform is built using the same Anthropic primitives it teaches (CLAUDE.md, `.claude/rules/`, slash commands, skills, subagents, MCP). Contributing a lesson is itself exam-prep.

Phase 1 contribution flow (Phase 5 will add `/new-lesson` to automate this):

1. Pick an unbuilt task statement from [docs/curriculum-map.md](docs/curriculum-map.md).
2. Create `lessons/module-N-<domain>/<task-id>-<slug>/` with `lesson.md`, `exercise.md`, `rubric.yaml`, and a `starter/` directory.
3. Follow the conventions in [.claude/rules/lesson-authoring.md](.claude/rules/lesson-authoring.md) and [.claude/rules/rubric-authoring.md](.claude/rules/rubric-authoring.md) — Claude Code will load these automatically when you edit a matching file.
4. Open a PR. Update the lesson's row in the curriculum map to `complete`.
