"""
P1 — Text Normalization: edge case handling
=============================================

clean_text() and normalize_diacritics() were built and tested against
fairly well-formed text (Bible, news). This module handles three patterns
that show up specifically in informal/social text and were NOT exercised
by Sprint 1's test suite:

1. Mixed-language text (Luganda sentences with embedded English words)
2. Numbers (phone numbers, prices, dates, tech abbreviations like "4G")
3. Emoji / symbols / hashtags / mentions

Design principle, consistent with the rest of P1: when in doubt, PRESERVE
rather than guess. Stripping or altering something we're not confident
about is worse than leaving it for a downstream module to handle with
better context.
"""

import re

# ---------------------------------------------------------------------------
# 1. Mixed-language text
# ---------------------------------------------------------------------------
# Decision: clean_text() and normalize_diacritics() do NOT attempt to detect
# or separate English words embedded in Luganda text (e.g. "stress" in
# "omusajja abadde ne stress z'awaka", log #7 from Sprint 1). Real examples
# confirm this is legitimate code-switching, not an error to fix. Language
# detection/tagging is a job for the tokenizer/spellchecker module, which
# has more context (a dictionary, a language model) to do it reliably.
#
# What THIS module guarantees: none of the number/emoji/punctuation
# handling below should corrupt embedded English words. That's covered by
# test_edge_cases.py using the real "stress" / "Chef" examples.


# ---------------------------------------------------------------------------
# 2. Numbers
# ---------------------------------------------------------------------------

# Short, usually-uppercase alphanumeric patterns that should stay glued to
# a preceding digit rather than getting a space inserted (log #10 handled
# the opposite case: "58Baliraanwa", a real word stuck to a number).
_SAFE_ABBREVIATION_RE = re.compile(r"^[A-Za-z]{1,3}$")
_KNOWN_GLUED_PATTERNS = {"g", "k", "d", "fa", "am", "pm"}  # 4g/5g, 4k, 3d, 2fa, 9am/5pm


def fix_number_word_spacing(text: str) -> str:
    """Insert a space between a digit and a following word — UNLESS the
    following letters look like a short tech/time abbreviation (4G, 3D,
    2FA, 9am), in which case leave it glued. Refines the Sprint 1 version,
    which would have incorrectly split "4G" into "4 G".
    """
    def _maybe_space(match):
        digit, letters = match.group(1), match.group(2)
        if (_SAFE_ABBREVIATION_RE.match(letters)
                and letters.lower() in _KNOWN_GLUED_PATTERNS):
            return match.group(0)
        return f"{digit} {letters}"

    return re.sub(r"(\d)([A-Za-zÀ-ÿ]+)", _maybe_space, text)


# Phone numbers (Ugandan formats: 0700123456, 0700 123 456, +256700123456,
# 0700-123-456) and currency amounts (50,000/=, UGX 50,000) should NOT have
# their internal punctuation touched by comma/spacing rules elsewhere in
# the pipeline. We don't need special-case code for this as long as those
# rules only ever touch punctuation immediately followed by whitespace —
# but we add explicit tests to prove it, since this is exactly the kind of
# thing that breaks silently.
PHONE_NUMBER_RE = re.compile(r"(\+?256|0)\d{2}[\s-]?\d{3}[\s-]?\d{3,4}")
CURRENCY_RE = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:/=)?")


def find_numeric_entities(text: str) -> dict:
    """Surface phone numbers / currency amounts found in text, so callers
    (or a future spellchecker) know which spans to treat as non-linguistic
    tokens rather than words to normalize or spell-check.
    """
    return {
        "phone_numbers": PHONE_NUMBER_RE.findall(text),
        "currency_amounts": CURRENCY_RE.findall(text),
    }


# ---------------------------------------------------------------------------
# 3. Emoji / symbols / hashtags / mentions
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # pictographs, emoticons, transport, supplemental symbols
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flags)
    "\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs
    "\U00002190-\U000021FF"  # arrows (occasionally used decoratively)
    "]+",
    flags=re.UNICODE,
)

_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_RE = re.compile(r"@\w+")


def extract_emoji(text: str) -> tuple[str, list[str]]:
    """Remove emoji from text, returning (text_without_emoji, emoji_found).

    Emoji are extracted rather than silently deleted: downstream modules
    (e.g. a future sentiment/tone component) may still want them, even
    though a spelling/morphology pipeline generally doesn't.
    """
    found = _EMOJI_RE.findall(text)
    # findall on a char-class-with-+ pattern can return multi-emoji runs as
    # single matches; split those into individual codepoints for clarity.
    individual = [ch for run in found for ch in run]
    cleaned = _EMOJI_RE.sub(" ", text)
    return cleaned, individual


def extract_hashtags_and_mentions(text: str) -> dict:
    """Surface hashtags/mentions without removing them from the text —
    these often carry meaning (e.g. an organization name) and default
    behavior is to preserve them in clean_text().
    """
    return {
        "hashtags": _HASHTAG_RE.findall(text),
        "mentions": _MENTION_RE.findall(text),
    }


def handle_social_edge_cases(text: str, strip_emoji: bool = True) -> str:
    """Apply number-spacing fix and (optionally) emoji stripping. Hashtags
    and mentions are left untouched by default — see rationale above.
    """
    text = fix_number_word_spacing(text)
    if strip_emoji:
        text, _ = extract_emoji(text)
        text = re.sub(r"[ \t]+", " ", text).strip()
    return text