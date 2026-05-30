"""Test fixtures for the multi-source synthesis exercise.

SOURCES mirrors the ``document_index -> document`` mapping the Citations feature
uses: a source_id resolves to a real source with a title. CLAIMS are already-
extracted {topic, statement, source_id, timestamp} records — including a topic
with two conflicting, differently-dated claims (the newer should win, the older
should be kept as an annotated conflict) and one claim whose source_id is NOT in
SOURCES (it must be dropped, never emitted unsourced).

REQUIRED_TOPICS asks for one topic ("churn") that no claim supports, so a correct
synthesizer reports it as a coverage gap.
"""

SOURCES = {
    "rep-2023": {"title": "Market Report 2023"},
    "rep-2025": {"title": "Market Report 2025"},
    "brief-a": {"title": "Analyst Brief A"},
}

CLAIMS = [
    # Conflicting topic: two dated claims for market_size; rep-2025 is newer and wins.
    {
        "topic": "market_size",
        "statement": "The market is $1.0B.",
        "source_id": "rep-2023",
        "timestamp": "2023-01-01",
    },
    {
        "topic": "market_size",
        "statement": "The market is $1.4B.",
        "source_id": "rep-2025",
        "timestamp": "2025-01-01",
    },
    # Single-source topic.
    {
        "topic": "growth_rate",
        "statement": "Growth is 8% YoY.",
        "source_id": "brief-a",
        "timestamp": "2024-06-01",
    },
    # Unsourced claim: source_id not in SOURCES. Must be dropped entirely.
    {
        "topic": "rumored_acquisition",
        "statement": "A competitor will be acquired.",
        "source_id": "unknown-blog",
        "timestamp": "2025-03-01",
    },
]

# "churn" is required but no claim supports it -> coverage gap.
REQUIRED_TOPICS = ["market_size", "growth_rate", "churn"]
