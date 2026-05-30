# Information provenance and uncertainty in multi-source synthesis — exercise

## What you're building

Implement `synthesize` in `synthesis.py`. It folds a list of already-extracted claims into one synthesis artifact that **keeps the trail back to the sources**: every item carries non-empty provenance, conflicts are resolved by recency but kept and annotated, unsourced claims are dropped, and required topics nobody covered are reported as gaps.

## Function signature

```python
def synthesize(claims, sources, required_topics=None):
    """
    Args:
        claims:          list[dict] — each {"topic", "statement", "source_id",
                         "timestamp"} where timestamp is an ISO date string.
        sources:         dict — source_id -> {"title": str}.
        required_topics: optional list[str] — topics the synthesis was asked to
                         cover; uncovered ones are reported as coverage gaps.

    Returns:
        dict with "items" (one per topic with a sourced claim) and
        "coverage_gaps" (required_topics with no supporting claim).
    """
```

Use the data in `fixtures.py` (`CLAIMS`, `SOURCES`, `REQUIRED_TOPICS`) — the tests import from it.

## Requirements

You must:

1. **Group claims by topic and resolve conflicts by recency.** When several claims share a topic, `resolved` is the statement of the claim with the **newest** `timestamp`.
2. **Attach non-empty `provenance` to every item.** Each item's `provenance` is a list of `{"source_id", "title"}` — the title looked up from `sources`. No item may be emitted with empty provenance.
3. **Keep losing claims under `conflicts`, annotated.** The non-winning claims for a topic go into `conflicts` as `{"statement", "source_id", "title", "timestamp", "annotation"}`, where `annotation` explains the claim was superseded by the newer source. Single-source topics have `conflicts == []`.
4. **Report coverage gaps.** Any topic in `required_topics` with no supporting claim goes into `coverage_gaps`. When `required_topics` is not given, `coverage_gaps` is `[]`.
5. **Pass every test in `test_synthesis.py`.**

You must NOT:

6. **Emit any claim without a source mapping.** A claim whose `source_id` is not in `sources` must be **dropped** — never emitted as an item, and never given a fabricated or empty source. This is the external-knowledge restriction: synthesize only from provided sources.
7. **Silently drop a conflicting source.** When two claims disagree, you may not keep only the winner and discard the other. The losing claim must survive in `conflicts` with its source and an annotation. Picking a side without recording the conflict fails the rubric.

Requirements 6 and 7 are graded directly (`check: anti_pattern`). The verifier reads your code for them; they fail the rubric whether or not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/7.6
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The exercise is pure deterministic logic — no Anthropic API, no network, no `ANTHROPIC_API_KEY`. It models the shape the Citations feature produces (each claim mapped to a `document_index` / `cited_text`) so you can see the provenance contract independent of a model call.

When you're ready (or stuck), run `/verify 7.6` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) — the `claim → source` mapping (`document_index`, `cited_text`, location) your `provenance` mirrors.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — external-knowledge restriction (drop unsourced claims) and reporting what you can't support.
