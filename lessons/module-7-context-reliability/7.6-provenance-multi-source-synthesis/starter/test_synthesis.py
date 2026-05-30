"""Tests for the multi-source synthesis exercise.

These are the contract: every item carries non-empty provenance, conflicts are
kept and annotated (newer wins), unsourced claims are dropped, and required
topics with no support are reported as coverage gaps.
"""
from fixtures import CLAIMS, REQUIRED_TOPICS, SOURCES
from synthesis import synthesize


def _item(result, topic):
    matches = [it for it in result["items"] if it["topic"] == topic]
    assert len(matches) == 1, "expected exactly one item for topic %r" % topic
    return matches[0]


def test_every_item_has_non_empty_provenance():
    result = synthesize(CLAIMS, SOURCES, REQUIRED_TOPICS)
    assert result["items"], "expected at least one synthesized item"
    for item in result["items"]:
        assert item["provenance"], "item %r has empty provenance" % item["topic"]
        for ref in item["provenance"]:
            assert ref["source_id"] in SOURCES
            assert ref["title"] == SOURCES[ref["source_id"]]["title"]


def test_no_item_lacks_a_source():
    # Stronger restatement: no item, and no provenance entry, may reference a
    # source that is not in SOURCES, and none may be unsourced.
    result = synthesize(CLAIMS, SOURCES, REQUIRED_TOPICS)
    for item in result["items"]:
        assert len(item["provenance"]) >= 1
        for ref in item["provenance"]:
            assert ref.get("source_id") in SOURCES


def test_unsourced_claim_is_dropped():
    # The "rumored_acquisition" claim points at a source_id not in SOURCES.
    result = synthesize(CLAIMS, SOURCES, REQUIRED_TOPICS)
    topics = {item["topic"] for item in result["items"]}
    assert "rumored_acquisition" not in topics


def test_conflict_resolves_to_newest_and_keeps_loser_annotated():
    result = synthesize(CLAIMS, SOURCES, REQUIRED_TOPICS)
    market = _item(result, "market_size")

    # Newest timestamp (rep-2025) wins the resolved value and provenance.
    assert market["resolved"] == "The market is $1.4B."
    assert any(ref["source_id"] == "rep-2025" for ref in market["provenance"])

    # The older claim is KEPT under conflicts (not dropped) and annotated.
    assert len(market["conflicts"]) == 1
    loser = market["conflicts"][0]
    assert loser["statement"] == "The market is $1.0B."
    assert loser["source_id"] == "rep-2023"
    assert loser["title"] == "Market Report 2023"
    assert loser["timestamp"] == "2023-01-01"
    assert loser["annotation"], "the dropped-from-resolution claim must be annotated"


def test_single_source_topic_has_no_conflicts():
    result = synthesize(CLAIMS, SOURCES, REQUIRED_TOPICS)
    growth = _item(result, "growth_rate")
    assert growth["resolved"] == "Growth is 8% YoY."
    assert growth["conflicts"] == []


def test_coverage_gaps_lists_uncovered_required_topic():
    result = synthesize(CLAIMS, SOURCES, REQUIRED_TOPICS)
    assert result["coverage_gaps"] == ["churn"]


def test_no_required_topics_means_no_gaps():
    result = synthesize(CLAIMS, SOURCES)
    assert result["coverage_gaps"] == []
