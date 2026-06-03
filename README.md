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

### Coach

Not sure what to do next? Let the coach read your history and build a plan:

```bash
/coach CCAF            # prioritized study plan: what to study/practice/verify next, and mock-exam readiness
```

`/coach` is a **hub-and-spoke coordinator**: it spawns the read-only **coach** subagent, which reads your progress (verify scores, mock-exam results) against the curriculum and exam maps and returns a prioritized plan — your weakest domains translated into the exact built chapters to study, the studied-but-unverified chapters that are one `/verify` from locked in, and whether you're ready to sit `/mock-exam CCAF`. The command then drives the top action for you (it can spawn the verifier or examiner directly to grade or quiz on the spot). Run it any time you finish a chapter or a mock and want to know where to point next.

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and authenticated
- `ANTHROPIC_API_KEY` exported in your shell (only needed to run exercise tests against the real API; the platform itself doesn't call the API)
- Python 3.10+ with `pip` (exercises use `pip install -r requirements.txt && pytest`)

## Status

**All five phases complete. All 37 of 37 chapters built.** The full platform is live: slash commands, automated grading (verifier + grading MCP server), assessment (examiner + `/practice`/`/mock-exam`), coaching (`/coach` hub-and-spoke coordinator + progress-tracking MCP server), and authoring commands (`/new-lesson`, `/new-question`). The complete 37-chapter learning path is in [docs/curriculum-map.md](docs/curriculum-map.md) with exam coverage in [docs/exam-mapping.md](docs/exam-mapping.md).

- **Phase 1** ✅ — Skeleton repo, slash commands, first lessons end-to-end
- **Phase 2** ✅ — Verifier subagent + grading MCP server (automated rubric checks)
- **Phase 3** ✅ — Examiner subagent, question bank, `/practice` and `/mock-exam`
- **Phase 4** ✅ — Coach subagent + `/coach` hub-and-spoke coordinator + progress-tracking MCP server
- **Phase 5** ✅ — Authoring commands `/new-lesson` + `/new-question` + full 37-chapter content build-out

## Development & tests

The repo ships its own test suite (platform infrastructure, not coursework). One command validates the whole project:

```bash
make install   # one-time: pip install -r requirements-dev.txt (needs Python 3.10+)
make test      # full suite: structural/content/integrity validation + MCP server tests
```

- **`make test-structure`** (`tests/`) — every lesson's frontmatter/references/rubric, the curriculum-map ↔ exam-mapping ↔ disk consistency, the question-bank schema (and that all 6 scenarios stay populated), and that every starter file compiles.
- **`make test-infra`** — the grading + progress MCP server unit tests.

CI runs the same suite on every push and PR via [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — the platform dogfooding the "Claude Code in CI/CD" material it teaches in chapter 5.7.

## Disclaimer

Unofficial. Not affiliated with, endorsed by, or sponsored by Anthropic. Built as exam-prep using the public [Claude Certified Architect — Foundations Certification Exam Guide](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F8lsy243ftffjjy1cx9lm3o2bw%2Fpublic%2F1773274827%2FClaude+Certified+Architect+%E2%80%93+Foundations+Certification+Exam+Guide.pdf) as the source of truth.

## License

MIT. See [LICENSE](LICENSE) (to be added).

## Contributing

The platform is built using the same Anthropic primitives it teaches (CLAUDE.md, `.claude/rules/`, slash commands, skills, subagents, MCP). Contributing a lesson is itself exam-prep.

Two authoring commands scaffold the work (they produce a structurally-valid skeleton and coach you through filling it — they don't write the lesson for you):

1. Pick an unbuilt chapter from [docs/curriculum-map.md](docs/curriculum-map.md).
2. Run `/new-lesson <chapter>` (e.g. `/new-lesson 2.1`). It scaffolds `lessons/<module>/<chapter>-<slug>/` with `lesson.md`, `exercise.md`, `rubric.yaml`, and a `starter/` — frontmatter, the six-section structure, weights summing to 100 with an anti-pattern, and a compiling starter all in place — then walks you through filling each piece per [.claude/rules/lesson-authoring.md](.claude/rules/lesson-authoring.md) and [.claude/rules/rubric-authoring.md](.claude/rules/rubric-authoring.md) (these load automatically when you edit a matching file).
3. Run `/new-question <chapter>` to seed that chapter's `practice.yaml`, or `/new-question CCAF` to add scenario questions to the mock-exam bank — both enforce [.claude/rules/question-authoring.md](.claude/rules/question-authoring.md) (one correct answer, three plausible distractors, an explanation that refutes each, every question traced to the guide).
4. Run the `lesson-auditor` on the chapter until it passes, flip the chapter to **built** in the curriculum map and exam mapping, and open a PR.
