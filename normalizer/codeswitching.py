"""
code_switching.py -- detects and tags English<->Luganda code-switching
in mixed text.

edge_cases.py already documents the project's stance on this (see its
"Mixed-language text" section): embedded English words are legitimate
code-switching, not an error to fix, and should be PRESERVED rather
than stripped or altered. That module explicitly punts the actual
detection/tagging job to "the tokenizer/spellchecker module, which has
more context" -- this module is that home.

APPROACH
--------
Lexicon-based, not a generic English-dictionary lookup (none is
bundled -- see DOCUMENTED LIMITATION below). A token is tagged:

    "LUG"  -- found in the project's known-Luganda word lists
              (data/nouns.txt, data/verbs.txt, stopwords.CLOSED_CLASS,
              spelling_dictionary.json keys+values)
    "ENG"  -- found in a small curated common-English-word list bundled
              in this module
    "NUM"  -- purely numeric
    "PUNCT"-- purely punctuation
    "UNK"  -- in neither lexicon; NOT guessed at, consistent with the
              "preserve rather than guess" project ethos

Each result also carries a `method` field ("lexicon" or "none") so
callers can see exactly how confident the tag is, rather than a bare
label that looks more authoritative than it is.

DOCUMENTED LIMITATION
-----------------------
The bundled English word list is a small, hand-picked set of common
function/content words (~120 entries) -- not a real English
dictionary. This module will under-detect English on any less-common
word (proper nouns, technical terms, slang) and should not be treated
as a general-purpose language identifier. Extend ENGLISH_COMMON_WORDS
deliberately, the same way spelling_dictionary.json is extended: only
with confirmed entries, not by guessing.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache

from .stopwords import CLOSED_CLASS

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Small, curated set of very common English words likely to appear via
# code-switching in Luganda social/news text. NOT an exhaustive English
# dictionary -- see module docstring.
ENGLISH_COMMON_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "am",
    "i", "you", "he", "she", "it", "we", "they", "this", "that", "these",
    "those", "and", "or", "but", "if", "so", "because", "for", "of",
    "to", "in", "on", "at", "by", "with", "from", "as", "not", "no",
    "yes", "ok", "okay", "please", "thanks", "thank", "sorry", "hello",
    "hi", "bye", "stress", "chef", "phone", "call", "text", "message",
    "network", "data", "internet", "wifi", "job", "work", "office",
    "school", "college", "university", "money", "cash", "bank", "account",
    "meeting", "boss", "manager", "project", "deadline", "report",
    "computer", "laptop", "email", "app", "update", "download", "upload",
    "video", "photo", "picture", "music", "song", "movie", "game",
    "team", "match", "score", "goal", "president", "minister",
    "government", "police", "hospital", "doctor", "nurse", "medicine",
    "traffic", "taxi", "bus", "car", "fuel", "petrol", "shop", "market",
    "price", "sale", "discount", "customer", "service", "delivery",
    "order", "receipt", "invoice", "tax", "budget", "loan", "interest",
    "insurance", "contract", "agreement", "lawyer", "court", "case",
    "news", "weather", "today", "tomorrow", "yesterday", "morning",
    "afternoon", "evening", "night", "week", "month", "year", "time",
}


def _read_word_column(filename: str) -> set[str]:
    """Read the first tab-separated column of a data file, skipping
    comments (#) and blank lines. Returns an empty set (not an error)
    if the file is missing -- this module should degrade gracefully,
    not crash, if the data directory changes shape."""
    path = os.path.join(_DATA_DIR, filename)
    words: set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                first_col = line.split("\t")[0].strip()
                if first_col:
                    words.add(first_col.lower())
    except (FileNotFoundError, OSError):
        pass
    return words


@lru_cache(maxsize=1)
def _luganda_lexicon() -> frozenset[str]:
    """Build the known-Luganda word set once and cache it: nouns.txt +
    verbs.txt surface forms, CLOSED_CLASS particles, and every key/value
    in the spelling dictionary (both the misspelling and its
    correction are real Luganda words)."""
    words: set[str] = set()
    words |= _read_word_column("nouns.txt")
    words |= _read_word_column("verbs.txt")
    words |= {w.lower() for w in CLOSED_CLASS}

    try:
        from .spelling import load_dictionary
        mappings = load_dictionary()
        for variant, canonical in mappings.items():
            words.add(variant.lower())
            words.add(canonical.lower())
    except Exception:
        pass  # spelling dictionary is optional context here, never fatal

    return frozenset(words)


_NUM_RE = re.compile(r"^-?\d+([.,]\d+)*$")
_PUNCT_RE = re.compile(r"^[^\w\s]+$", re.UNICODE)


def tag_token(token: str) -> dict:
    """Classify a single token. Returns
    {"token": token, "tag": "LUG"|"ENG"|"NUM"|"PUNCT"|"UNK", "method": "lexicon"|"none"}.
    """
    if _NUM_RE.match(token):
        return {"token": token, "tag": "NUM", "method": "none"}
    if _PUNCT_RE.match(token):
        return {"token": token, "tag": "PUNCT", "method": "none"}

    lowered = token.lower().strip(".,!?;:\"'()")
    if lowered in _luganda_lexicon():
        return {"token": token, "tag": "LUG", "method": "lexicon"}
    if lowered in ENGLISH_COMMON_WORDS:
        return {"token": token, "tag": "ENG", "method": "lexicon"}
    return {"token": token, "tag": "UNK", "method": "none"}


def tag_tokens(tokens: list[str]) -> list[dict]:
    """Classify a whole token list. See tag_token for the per-token shape."""
    return [tag_token(t) for t in tokens]


def has_code_switching(tokens: list[str]) -> bool:
    """True if the token list contains at least one lexicon-confirmed
    Luganda token AND at least one lexicon-confirmed English token --
    i.e. actual detected code-switching, not just "some unknown words."
    """
    tags = {t["tag"] for t in tag_tokens(tokens) if t["method"] == "lexicon"}
    return "LUG" in tags and "ENG" in tags


def annotate_code_switching(text: str) -> str:
    """Wrap detected English spans in `text` with [ENG]...[/ENG] markers,
    leaving Luganda and unknown tokens untouched. This is an explicit,
    reversible ANNOTATION -- it never deletes or rewrites the original
    words, consistent with edge_cases.py's "preserve rather than guess"
    principle for mixed-language text. Intended for callers that want
    to *see* the code-switch boundaries (e.g. for corpus study), not as
    a step in the default normalize() pipeline.
    """
    words = text.split(" ")
    out = []
    for word in words:
        stripped = word.strip(".,!?;:\"'()")
        trailing = word[len(stripped):] if stripped else ""
        leading_len = len(word) - len(word.lstrip(".,!?;:\"'()"))
        leading = word[:leading_len]
        core = word[leading_len:len(word) - len(trailing)] if trailing else word[leading_len:]
        tag = tag_token(core)
        if tag["tag"] == "ENG" and tag["method"] == "lexicon":
            out.append(f"{leading}[ENG]{core}[/ENG]{trailing}")
        else:
            out.append(word)
    return " ".join(out)