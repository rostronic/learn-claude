---
chapter: "7.6"
slug: "provenance-multi-source-synthesis"
title: "Information provenance and uncertainty in multi-source synthesis"
module: "module-7-context-reliability"
sequence: 33
references:
  - title: "Citations"
    url: "https://platform.claude.com/docs/en/build-with-claude/citations"
    type: official_docs
    covers: "Claim → source mapping with cited_text, document_index, and a location; guaranteed valid pointers"
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "External knowledge restriction, verify-with-citations (retract unsupported claims), allow 'I don't know'"
  - title: "Increase output consistency"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency"
    type: official_docs
    covers: "Retrieval grounding, ask for clarification when unsure, constrained output"
---

# Information provenance and uncertainty in multi-source synthesis

## Overview

When Claude reads several documents and produces one answer, the synthesis is only as trustworthy as the **trail back to the sources**. A summary that blends three reports into a single confident paragraph is a liability: a reader can't tell which sentence came from which document, can't catch a fabricated claim, and can't see that two of the sources actually disagreed. Task Statement 5.6 is about building synthesis that **keeps that trail intact** — every claim mapped to a source, conflicts surfaced rather than silently resolved, gaps in coverage reported rather than papered over, and nothing asserted that no source supports.

This sits at the reliability end of Domain 5. The other Domain 5 chapters keep *Claude's own* context healthy across a long task; this one is about the **output contract** of a synthesis step: when you fold N sources into one artifact, what guarantees does that artifact carry? The Anthropic answer is concrete. The platform ships a **Citations** feature whose entire job is to attach a verifiable `claim → source` pointer to each piece of generated text ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)), and the hallucination-reduction guidance tells you to **verify with citations and retract any claim a source doesn't support** ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). Provenance isn't a nice-to-have you bolt on after; it's the shape the synthesis should have from the start.

This lesson builds a small, deterministic synthesizer that enforces those guarantees in code — so you can see the contract independent of any one model call.

## How it works

Four properties define trustworthy multi-source synthesis. Each one has a concrete mechanism behind it in the official docs.

**1. Claim → source mapping (mirror the Citations shape).** The Citations feature makes Claude's response a list of text blocks: "Responses may now include multiple text blocks where each text block can contain a claim that Claude is making and a list of citations that support the claim" ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)). A citation carries three things worth copying into any provenance model:

- `document_index` — *which* source (an integer index into the documents you supplied),
- `cited_text` — the exact span from that source the claim rests on, and
- a **location** (`char_location`, `page_location`, or `content_block_location`) pinning where in the source it came from.

The critical property is that these pointers are **guaranteed valid** — Citations returns references "guaranteed to contain valid pointers to the provided documents" ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)). When you design your own synthesis output, you mirror that shape: every claim travels with a non-empty list of source references. A claim with no source reference is, by construction, not allowed to exist.

**2. External-knowledge restriction.** Synthesis must draw *only* from the provided sources, not from the model's parametric memory. The hallucination guidance is explicit: instruct Claude to "only use information from provided documents and not its general knowledge" ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). The same page prescribes the verification step: have Claude extract word-for-word quotes and then **verify with citations** — verifying each of its claims by citing the source, and retracting any claim it cannot cite ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). In a deterministic synthesizer, this becomes a hard invariant: a claim is admitted to the output **iff** it resolves to a real source; an unsourced claim is dropped, not emitted with a hedge.

**3. Temporal handling and conflict annotation.** Real source sets disagree, and often the disagreement is just *staleness* — an old report says one thing, a newer one corrects it. The wrong move is to silently pick a winner; the reader then has no idea a conflict ever existed. The right move borrows from the consistency guidance, which tells you to ground answers in retrieved sources rather than letting the model improvise ([Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)), and from the hallucination guidance's instruction to let Claude say "I don't know" rather than guess ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). Applied to conflicts, the rule is: **prefer the newer source for the resolved value, but keep the losing claims and annotate the resolution.** The conflict stays in the record with its sources attached, so a reader sees both what you concluded and what you set aside, and why.

**4. Coverage-gap reporting.** If you were asked to cover topics A, B, and C and the sources only support A and B, a synthesis that quietly omits C *implies* complete coverage of everything it does mention — a subtle hallucination of completeness. The fix is the same family as "allow Claude to say 'I don't know'": list the required topics that have **no supporting source** as an explicit gap, rather than letting silence read as coverage ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)).

Here's the Citations shape these properties mirror — the request side enables it per-document, and the response interleaves cited text blocks:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "text", "media_type": "text/plain",
                               "data": "Q3 revenue was $4.2M, up 12% YoY."},
                    "title": "Q3 Report",
                    "citations": {"enabled": True},   # turn on claim → source mapping
                },
                {"type": "text", "text": "Summarize the revenue figures."},
            ],
        }
    ],
)

# Each text block in the response carries its own provenance.
for block in response.content:
    if block.type == "text":
        for c in (block.citations or []):
            print(block.text, "->", c.document_index, repr(c.cited_text))
```

Every emitted sentence comes back with a `citations` list whose entries name `document_index` and the `cited_text` they rest on. Our exercise builds the deterministic analogue of this: a `synthesize()` function that produces items each carrying a non-empty `provenance` list, resolves conflicts by recency while keeping the losers, and reports coverage gaps.

## Worked example

We model a synthesis step over already-extracted claims. Each claim is a dict — `{topic, statement, source_id, timestamp}` — where `timestamp` is an ISO date string and `source_id` indexes into a `sources` map (`source_id -> {title}`), exactly the way a `document_index` indexes into supplied documents.

```python
SOURCES = {
    "rep-2023": {"title": "Market Report 2023"},
    "rep-2025": {"title": "Market Report 2025"},
    "brief-a":  {"title": "Analyst Brief A"},
}

CLAIMS = [
    {"topic": "market_size", "statement": "The market is $1.0B.",
     "source_id": "rep-2023", "timestamp": "2023-01-01"},
    {"topic": "market_size", "statement": "The market is $1.4B.",
     "source_id": "rep-2025", "timestamp": "2025-01-01"},     # newer — wins
    {"topic": "growth_rate", "statement": "Growth is 8% YoY.",
     "source_id": "brief-a", "timestamp": "2024-06-01"},
]

result = synthesize(CLAIMS, SOURCES, required_topics=["market_size", "growth_rate", "churn"])
```

`synthesize` groups claims by topic, then for each topic produces one item:

```python
{
    "topic": "market_size",
    "resolved": "The market is $1.4B.",                    # newest timestamp wins
    "provenance": [{"source_id": "rep-2025", "title": "Market Report 2025"}],
    "conflicts": [                                          # losers kept, annotated
        {
            "statement": "The market is $1.0B.",
            "source_id": "rep-2023",
            "title": "Market Report 2023",
            "timestamp": "2023-01-01",
            "annotation": "superseded by newer source rep-2025 (2025-01-01)",
        }
    ],
}
```

Two invariants do the real work. First, **`provenance` is always non-empty** — the resolved statement's source is looked up in `SOURCES` and attached; if a claim's `source_id` isn't in `SOURCES`, that claim is *dropped*, never emitted unsourced (the external-knowledge restriction, enforced structurally). Second, **conflicting claims are kept, not discarded** — the older `market_size` claim lands in `conflicts` with an `annotation` explaining why it lost (a newer source superseded it). Nothing is silently chosen.

Coverage gaps fall out of the `required_topics` argument:

```python
result["coverage_gaps"]   # -> ["churn"]   (asked for, but no claim supports it)
```

`churn` was required but no claim mentions it, so it's reported as a gap rather than omitted. The full return value is:

```python
{
    "items": [ {market_size item}, {growth_rate item} ],
    "coverage_gaps": ["churn"],
}
```

A reader can now audit the synthesis end to end: every item names its source, the one disagreement is on the record with the reason it was resolved that way, and the topic nobody covered is flagged instead of implied.

## Anti-patterns & pitfalls

These are the wrong approaches the exam dangles in front of you. Each one breaks one of the four properties above.

1. **Blended, unsourced synthesis.** Folding all the sources into one fluent paragraph with no per-claim attribution. This is the default thing a naive prompt produces, and it's wrong: the reader cannot verify any sentence, and a fabricated claim is indistinguishable from a real one. Anthropic's prescription is the opposite — use Citations so each text block can carry a claim and the list of citations that support it, mapping the claim to its source ([Citations](https://platform.claude.com/docs/en/build-with-claude/citations)). In our model this is the non-negotiable rule that **no item may be emitted without non-empty `provenance`**.

2. **Silently picking one side of a conflict.** Two sources disagree; the synthesizer quietly emits one value and drops the other. The reader never learns there was a disagreement, so they can't apply their own judgment. **Never silently resolve a conflict.** Prefer the newer source for the *resolved* value, but keep the losing claims in a `conflicts` list with an annotation — grounding the answer in the actual sources rather than improvising a single confident number ([Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)).

3. **Using the model's own knowledge to fill gaps.** When a source is silent, letting Claude reach into its parametric memory to "complete" the answer. This is exactly what the external-knowledge restriction forbids: instruct the model to "only use information from provided documents and not its general knowledge," and **retract any claim it cannot cite** ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). A claim that doesn't resolve to a provided source is dropped, not smoothed over.

4. **Implying complete coverage by staying silent on missing topics.** Omitting the topics no source covered, so the output reads as if everything asked for was answered. This manufactures a false sense of completeness. The correct behavior mirrors "allow Claude to say 'I don't know'" — surface the uncovered required topics as an explicit `coverage_gaps` list ([Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)).

The through-line: trustworthy synthesis is **auditable**. Every claim must be traceable to a source, every conflict must be visible, and every gap must be named. "It reads well and sounds confident" is not the bar — and on this exam, the confident-but-unsourced option is always the wrong answer.

## Exam focus

Task Statement 5.6 powers the synthesis steps inside the research and extraction scenarios:

- **Scenario 3 (Multi-Agent Research System)** — subagents each return findings from their own sources; the coordinator's job is to synthesize them *with provenance intact*, surfacing where subagents' sources disagree rather than averaging them into one confident claim.
- **Scenario 6 (Structured Data Extraction)** — extracting one record from multiple overlapping documents forces conflict resolution and coverage reporting: which document won a field, and which required fields no document supported.

Expect distractors that reward fluency over traceability: the option that produces the cleanest single paragraph, the one that "resolves" a conflict by just picking a number, the one that fills a missing field from general knowledge. The correct answer always preserves the claim → source mapping, keeps conflicts on the record (newer wins, losers annotated), restricts to provided sources, and reports gaps explicitly.

## References & further reading

- [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) — the feature that attaches a `claim → source` pointer (`document_index`, `cited_text`, location) to each generated sentence, with guaranteed-valid references. The shape our provenance model mirrors.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — external-knowledge restriction, "verify with citations" / retract-the-unsupported-claim, and "allow Claude to say 'I don't know'" — the basis for dropping unsourced claims and reporting coverage gaps.
- [Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — grounding answers in retrieved sources and asking for clarification when unsure rather than improvising; the basis for annotating conflicts instead of silently resolving them.

## Exam coverage

- **CCAF** — Domain 5 (Context Management & Reliability), Task Statement 5.6: Preserve information provenance and handle uncertainty in multi-source synthesis.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
