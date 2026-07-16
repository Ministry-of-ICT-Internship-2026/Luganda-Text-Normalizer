"""
abbreviations.py -- expands abbreviations and acronyms found in
Luganda text: government/organization acronyms (URA, KCCA, ...),
honorific titles (Dr, Prof, ...), and a small set of Latin
cross-language abbreviations that show up in Luganda writing via
code-switching (etc, e.g., i.e.).

Same architecture as spelling.py: a JSON-backed variant/acronym ->
expansion table, loaded once, with unknown input always passed
through unchanged (never crash, never guess an expansion that isn't
in the table).

DESIGN PRINCIPLE: organization acronyms are matched CASE-SENSITIVELY
(an acronym's casing is part of its identity -- "ura" lowercase in
running Luganda text is not obviously the Uganda Revenue Authority),
while honorific titles and cross-language abbreviations are matched
case-insensitively, matching how spelling.py treats ordinary words.
"""

from __future__ import annotations

import json
import os
import re

DEFAULT_DICT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "abbreviations_dictionary.json"
)


def load_abbreviations(path: str = DEFAULT_DICT_PATH) -> dict:
    """Load and flatten the abbreviations JSON into two lookup tables:
    {"case_sensitive": {...}, "case_insensitive": {...}}.

    Returns empty tables on any failure (missing file, corrupt JSON),
    so a broken dictionary file degrades to a no-op rather than
    breaking the whole pipeline -- same safety property as
    spelling.load_dictionary.
    """
    empty = {"case_sensitive": {}, "case_insensitive": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return empty

    case_sensitive = dict(data.get("organizations", {}))
    case_insensitive = {}
    case_insensitive.update(data.get("titles", {}))
    case_insensitive.update(data.get("cross_language", {}))
    return {"case_sensitive": case_sensitive, "case_insensitive": case_insensitive}


def _build_pattern(keys: list[str]) -> re.Pattern | None:
    """Build a single alternation regex matching any of `keys` as a whole
    "word", using (?<!\\w)/(?!\\w) lookarounds rather than \\b.

    Plain \\b breaks for keys like "e.g." or "i.e." that end in a
    period: "." is not a word character, so \\b never fires between a
    trailing "." and a following space -- the naive \\bkey\\b pattern
    would silently never match those keys. (?<!\\w) / (?!\\w) instead
    just assert "not immediately preceded/followed by a word
    character," which is correct whether the key's own edge is a
    letter (Dr, URA) or punctuation (e.g., i.e.).
    """
    if not keys:
        return None
    # Longest-first so e.g. "e.g." isn't partially shadowed by a shorter key.
    ordered = sorted(keys, key=len, reverse=True)
    alternation = "|".join(re.escape(k) for k in ordered)
    return re.compile(r"(?<!\w)(" + alternation + r")(?!\w)")


def expand_abbreviations(text: str, tables: dict | None = None) -> str:
    """Replace known abbreviations/acronyms in `text` with their full
    expansion. Trailing punctuation directly after a match (a period
    ending an abbreviation like "Dr.") is preserved.

    Args:
        text: input string.
        tables: optional pre-loaded {"case_sensitive": {...},
            "case_insensitive": {...}} dict (as returned by
            load_abbreviations). If None, loads the default dictionary.

    Unknown text passes through unchanged -- this fallback is the
    critical safety property, same as spelling.standardize_spelling.
    """
    if tables is None:
        tables = load_abbreviations()
    if not text:
        return text

    case_sensitive = tables.get("case_sensitive", {})
    case_insensitive = tables.get("case_insensitive", {})

    cs_pattern = _build_pattern(list(case_sensitive.keys()))
    if cs_pattern is not None:
        text = cs_pattern.sub(lambda m: case_sensitive[m.group(1)], text)

    if case_insensitive:
        lookup = {k.lower(): v for k, v in case_insensitive.items()}
        ci_pattern = _build_pattern(list(case_insensitive.keys()))
        if ci_pattern is not None:
            ci_pattern = re.compile(ci_pattern.pattern, re.IGNORECASE)
            text = ci_pattern.sub(lambda m: lookup[m.group(1).lower()], text)

    return text