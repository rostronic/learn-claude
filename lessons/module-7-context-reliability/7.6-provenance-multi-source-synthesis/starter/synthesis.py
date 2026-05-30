"""Multi-source synthesis with provenance, conflict annotation, and gap reporting.

Implement ``synthesize`` per the docstring below. See the lesson and exercise.md.
"""
from typing import Any, Dict, List, Optional


def synthesize(claims, sources, required_topics=None):
    """Fold per-topic claims into one provenance-preserving synthesis.

    Args:
        claims: list of dicts, each {"topic": str, "statement": str,
                "source_id": str, "timestamp": str (ISO date, e.g. "2025-01-01")}.
        sources: dict mapping source_id -> {"title": str}.
        required_topics: optional list of topic names the synthesis was asked to
                cover. Topics in this list that no surviving claim supports are
                reported under "coverage_gaps".

    Returns:
        dict with:
          "items": one entry per topic that has at least one *sourced* claim, each:
              {
                "topic": str,
                "resolved": str,            # statement of the NEWEST-timestamp claim
                "provenance": [{"source_id": str, "title": str}],  # MUST be non-empty
                "conflicts": [              # the other competing claims, KEPT not dropped
                    {"statement": str, "source_id": str, "title": str,
                     "timestamp": str, "annotation": str},
                    ...
                ],
              }
          "coverage_gaps": list of required_topics (if given) with NO supporting claim.

    Rules (enforced structurally):
      - A claim whose source_id is not in ``sources`` is DROPPED (external-knowledge
        restriction): never emit an item or provenance entry without a real source.
      - Never emit an item whose "provenance" is empty.
      - When several sourced claims share a topic, "resolved" is the newest-timestamp
        claim; the rest go into "conflicts" (kept, annotated), never silently dropped.
    """
    # TODO 1: Group claims by topic, keeping ONLY claims whose source_id is in
    #         ``sources`` (drop unsourced claims — do not emit them anywhere).
    # TODO 2: For each topic with >= 1 sourced claim, sort its claims by timestamp;
    #         the newest is the resolved claim, the rest are conflicts.
    # TODO 3: Build the item: topic, resolved (newest statement), provenance
    #         (non-empty: the resolved claim's source_id + looked-up title), and
    #         conflicts (each older claim with source_id, title, timestamp, and an
    #         annotation explaining it was superseded by the newer source).
    # TODO 4: Build coverage_gaps: for each topic in required_topics (if provided)
    #         that has NO surviving sourced claim, add it to the gaps list.
    # TODO 5: Return {"items": [...], "coverage_gaps": [...]}.
    raise NotImplementedError("Implement synthesize() per the docstring and exercise.md")
