"""
P1 — Text Normalization: clean_text()
======================================

Implements the Bucket A (mechanical) rules identified in the P1 research log
(P1_Research_Log.xlsx) from inspecting real Luganda text sourced from Bukedde
news, Twitter/X, and the Luganda Revised Bible.

This module deliberately does NOT touch anything from Bucket B (diacritic /
spelling variants like the ŋ vs. ng' finding) — those require native-speaker
sign-off and belong in normalize_diacritics(), a separate function built
after that review happens.

Each rule below is traceable back to a specific log entry (see docstring
references to log IDs #1-#7). Number-spacing and emoji handling are now
implemented in edge_cases.py (Sprint 2) and imported here.
"""

import re
import unicodedata

from .edge_cases import fix_number_word_spacing, extract_emoji

# --- Quote / punctuation character maps -------------------------------------

_QUOTE_MAP = {
    "\u201c": '"', "\u201d": '"',   # curly double quotes -> straight  (log #5)
    "\u2018": "'", "\u2019": "'",   # curly single quotes -> straight
}

_DASH_MAP = {
    "\u2013": "-", "\u2014": "-",   # en dash / em dash -> hyphen
}

# Non-printable / control characters to strip outright (keep \n for now,
# it's handled separately by collapse_whitespace).
_CONTROL_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\xa0\u200b\u200c\u200d\ufeff]"
)


def normalize_unicode(text: str) -> str:
    """Normalize to NFC so visually-identical characters are byte-identical.

    Important prerequisite: a large share of "diacritic inconsistency" in
    scraped text is actually an encoding artifact (combining characters vs.
    precomposed characters), not a real spelling variant. Doing this first
    means Bucket B work only has to deal with genuine variants.
    """
    return unicodedata.normalize("NFC", text)


def strip_control_characters(text: str) -> str:
    """Remove non-printable / invisible characters (zero-width spaces, etc.)."""
    return _CONTROL_CHARS_RE.sub(" ", text)


def standardize_quotes_and_dashes(text: str) -> str:
    """Curly quotes -> straight quotes; en/em dash -> hyphen. (log #5)"""
    for variant, canonical in {**_QUOTE_MAP, **_DASH_MAP}.items():
        text = text.replace(variant, canonical)
    return text


def fix_spacing_before_punctuation(text: str) -> str:
    """Remove whitespace immediately before , . ; : ! ?  (log #4)"""
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def collapse_repeated_punctuation(text: str, max_repeat: int = 1) -> str:
    """Collapse runs of !, ?, . to at most `max_repeat` characters. (log #6)

    Default collapses fully (e.g. "!!!!" -> "!") since downstream tokenizers
    generally expect single punctuation marks. If preserving emphasis matters
    for a given task, call with max_repeat=2 or skip this step — this was
    flagged in the log as needing a team decision, not a settled default.
    """
    def _collapse(match):
        ch = match.group(0)[0]
        return ch * max_repeat
    return re.sub(r"([!?.])\1+", _collapse, text)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs to one space, and collapse 3+ newlines
    (irregular mid-sentence breaks, log #2) down to a single paragraph break,
    while still allowing single blank lines to separate paragraphs.
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # A lone newline in the middle of a sentence (not part of a genuine
    # paragraph break) is joined with a space.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)  # re-collapse any new doubles created above
    return text.strip()


def clean_text(text: str, collapse_punctuation: bool = True, strip_emoji: bool = True) -> str:
    """Run the full Bucket A cleaning pipeline in order.

    NOTE: This function intentionally does NOT strip stray non-Luganda
    caption artifacts like the "Portrait" example (log #1). That pattern is
    too easy to confuse with legitimate short English loanwords / code-
    switching (log #7, e.g. "stress", "Chef") to safely automate with a
    generic rule. Handle known scraping artifacts with a source-specific
    pre-filter before calling clean_text(), rather than baking a guess into
    the shared pipeline.

    Mixed-language text (English words embedded in Luganda) is left
    untouched by every step below — see edge_cases.py for the reasoning.
    """
    text = normalize_unicode(text)
    text = strip_control_characters(text)
    text = standardize_quotes_and_dashes(text)
    text = fix_number_word_spacing(text)
    if strip_emoji:
        text, _ = extract_emoji(text)
    text = fix_spacing_before_punctuation(text)
    if collapse_punctuation:
        text = collapse_repeated_punctuation(text)
    text = collapse_whitespace(text)
    return text