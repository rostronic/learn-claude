# Learn Claude

An open-source, Claude Code-native platform for **learning to build with Claude** — and for preparing for Anthropic's certification exams. Clone the repo, open Claude Code, type `/study 3.1`, and work through a dependency-ordered learning path of hands-on lessons. Lessons are exam-agnostic; an exam overlay maps each exam's task statements to the chapters that cover them (the first being the **Claude Certified Architect — Foundations**, CCAF — see [docs/exam-mapping.md](docs/exam-mapping.md)). Each lesson ends in a coding exercise graded against a rubric.

## Quick start

```bash
git clone <this-repo> learn-claude
cd learn-claude
pip install -r infra/grading-mcp/requirements.txt   # one-time: deps for the grading server
claude                 # open Claude Code (approve the "learn-claude-grading" MCP server when prompted)
/study 3.1             # walks you through chapter 3.1 — Agentic loops
/exercise 3.1          # copies the starter to ~/learn-claude-work/3.1/
/verify 3.1            # grades your work against the rubric, results in ~/learn-claude-work/3.1/results
```

The repo ships a project [`.mcp.json`](.mcp.json) that registers the **grading MCP server** (`infra/grading-mcp/`). Claude Code offers to start it when you open the repo, so it's running by the time you reach `/verify`; `/verify` grades through it (and falls back to running the checks directly if you decline). See [infra/grading-mcp/README.md](infra/grading-mcp/README.md) for details.

Studying for a specific certification? Run the course in that exam's order instead of course order:

```bash
/exam CCAF             # lists CCAF's task statements in exam order, walks the built chapters
```

### Assess

Once you've studied a chapter, test recall with multiple-choice questions before (or instead of) the coding exercise:

```bash
/practice 3.1          # one practice question for chapter 3.1 — hidden answer, revealed after you commit
/mock-exam CCAF        # a full, timed, domain-weighted mock exam — scaled score out of 1000, pass 720
```

Both route through the read-only **examiner** subagent, which holds the answer key so the chat never does — you answer honestly, then it reveals the rationale (and, for the mock exam, a per-domain breakdown plus which chapters to review). `/mock-exam` randomly draws 4 of the 6 exam scenarios and ~30 domain-weighted questions each run, and saves your result to `~/learn-claude-work/mock-exams/<CODE>/` (outside the repo). The scaled score is an approximation of Anthropic's scoring model, not the official algorithm.

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and authenticated
- `ANTHROPIC_API_KEY` exported in your shell (only needed to run exercise tests against the real API; the platform itself doesn't call the API)
- Python 3.10+ with `pip` (exercises use `pip install -r requirements.txt && pytest`)

## Status

**Phases 1–3 done; Phase 4 in progress.** The platform (slash commands, automated grading via the verifier + grading MCP server, and assessment via the examiner + `/practice`/`/mock-exam`) is built. **Seven of 37 chapters** are authored — Module 1 (1.1 Prompting with explicit criteria, 1.2 Few-shot prompting, 1.3 Structured output) and Module 3 (3.1 Agentic loops, 3.2 Coordinator and subagent orchestration, 3.3 Subagent invocation and context passing, 3.4 Distributing tools across agents & tool choice). The full 37-chapter learning path is mapped in [docs/curriculum-map.md](docs/curriculum-map.md) (with exam coverage in [docs/exam-mapping.md](docs/exam-mapping.md)); the rest are built out in Phase 5.

- **Phase 1** ✅ — Skeleton repo, slash commands, first lessons end-to-end
- **Phase 2** ✅ — Verifier subagent + grading MCP server (automated rubric checks)
- **Phase 3** ✅ — Examiner subagent, question bank, `/practice` and `/mock-exam`
- **Phase 4** (current) — Coach subagent (hub-and-spoke coordinator) + progress tracking
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
