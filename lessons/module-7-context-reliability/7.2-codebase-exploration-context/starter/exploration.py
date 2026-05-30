"""Context-efficient codebase exploration helpers.

Implement the three functions below. They are the deterministic core of the
exploration pipeline from the lesson: search-first selection, verbose-output
trimming, and position-aware ordering. Pure logic — no Anthropic API, no network.

Target Python 3.9.
"""

from typing import List, Dict, Any


def select_files(query: str, index: List[Dict[str, str]], max_files: int = 5) -> List[str]:
    """Search-first file selection: rank index entries by keyword overlap with the
    query and return the top max_files paths (a SUBSET, never the whole index).

    Args:
        query:     what the agent is looking for (e.g. "user login and session").
        index:     list of {"path": str, "summary": str} entries.
        max_files: cap on how many paths to return.

    Returns:
        At most max_files paths, ranked most-relevant-first by the number of query
        terms that overlap each entry's path + summary.
    """
    # TODO 1: tokenize the query into a set of terms (lowercase; you may drop
    #         common stopwords like "and"/"the" so they don't create spurious matches).
    # TODO 2: for each entry, tokenize its path + " " + summary and count how many
    #         of those tokens are in the query term set (the overlap score).
    # TODO 3: keep only entries with overlap > 0, sort by overlap descending.
    # TODO 4: return the top max_files paths (a subset — do NOT return the whole index).
    raise NotImplementedError("Implement select_files")


def trim_output(text: str, max_lines: int = 50) -> str:
    """Cap verbose tool output and mark the truncation.

    Args:
        text:      possibly long tool output (e.g. a file read or directory listing).
        max_lines: maximum number of lines to keep.

    Returns:
        text unchanged if it has <= max_lines lines; otherwise the first max_lines
        lines followed by a marker like "... [truncated N lines]" reporting how many
        lines were dropped.
    """
    # TODO 1: split text into lines.
    # TODO 2: if there are <= max_lines lines, return text unchanged.
    # TODO 3: otherwise keep the first max_lines lines, count the dropped lines, and
    #         append a truncation marker that reports that count.
    raise NotImplementedError("Implement trim_output")


def order_by_relevance(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Position-aware ordering: return chunks sorted by "score" descending so the
    most-relevant chunk leads and is not buried (countering context rot).

    Args:
        chunks: list of {"path": str, "score": number} dicts.

    Returns:
        The same chunks, ordered highest "score" first.
    """
    # TODO 1: sort chunks by the "score" key, descending, and return the result.
    raise NotImplementedError("Implement order_by_relevance")
