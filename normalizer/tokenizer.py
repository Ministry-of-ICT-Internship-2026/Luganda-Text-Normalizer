"""
luganda_normalizer.tokenizer
=============================
Tokenization module for Luganda text.

WHERE NLTK'S DEFAULT TOKENIZER BREAKS ON LUGANDA (empirically verified —
see tests/test_tokenizer.py::test_diagnostic_default_nltk_breaks)
--------------------------------------------------------------------------
nltk.word_tokenize() uses the Penn Treebank rules, built for English.

Luganda marks vowel elision at word boundaries with an apostrophe, e.g.
ne + ekitabo -> n'ekitabo ("and the book"), or nga + enda -> Ng'enda
("as I go"). The same apostrophe also appears inside "ng'", the typed
substitute for the letter ŋ.

You'd expect NLTK's English contraction rule (the one that splits
"don't" -> "do" + "n't") to wrongly chop these up. Testing shows it
mostly does NOT for the straight apostrophe ' — Treebank's rule only
fires on a fixed whitelist of English suffixes (n't, 's, 're, 've, 'll,
'd, 'm), and Luganda elisions don't match any of them, so they survive
as single tokens by coincidence, not by design.

The CONFIRMED breakage is the curly/typographic apostrophe ’ (U+2019)
instead of the straight ' (U+0027) — the default output of Word, Google
Docs, most phones, and most published Luganda text (autocorrect converts
' to ’). NLTK treats ’ as standalone punctuation and splits both sides:

    n'ekitabo   -> ["n'ekitabo"]              (straight quote: survives)
    n'ekitabo   -> ['n', '’', 'ekitabo']       (curly quote: destroyed)

A SECOND breakage (found via test 05_abbreviation_period_not_sentence_end)
appears once masking is introduced: NLTK relies on recognizing a small
whitelist of known abbreviations (e.g. "Dr", "Mr", "Prof") to decide a
trailing period isn't sentence-ending. Since our masking replaces words
with placeholders BEFORE NLTK runs, NLTK no longer sees "Dr" — it sees
an unfamiliar placeholder followed by a period, and splits the period
off as its own token:

    Dr. Musisi   -> expected ['Dr.', 'Musisi', ...]
    Dr. Musisi   -> got      ['Dr', '.', 'Musisi', ...]   (bug)

Fix: protect known abbreviations (word + trailing period, as one unit)
the same way elision words are protected — mask them before NLTK ever
sees the text, so there's no lone trailing period left to misread.

A THIRD breakage (found via test_tokenizer_extreme.py cases 16-17) is
independent of Luganda linguistics entirely: it's a namespace collision
in the masking mechanism itself. If the raw input text happens to
already contain something shaped like our internal placeholder tag
(e.g. a product code or ticket ID like "XLGWRDX0"), the restore step
could previously either crash with KeyError (if that exact index was
never generated) or, worse, silently substitute in an unrelated word
(if the index DID coincide with a real placeholder). Fixed by making
the placeholder tag a per-call random token that is verified absent
from the source text before use, rather than a fixed constant — see
Rule 8 below.

Everything else (agglutination, geminate consonants like "ssomero", long
vowels like "eddiini") is fine for NLTK at the word level, since those
aren't punctuation.
"""

from __future__ import annotations

import re
import secrets
from typing import Dict, List, Match, Optional

import nltk

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import word_tokenize as _nltk_word_tokenize

__all__ = ["tokenize", "diagnose"]


# ---------------------------------------------------------------------------
# CUSTOM RULES
# ---------------------------------------------------------------------------

# Rule 1 — apostrophe-aware word boundary.
# A Luganda "word" is letters (including ŋ/Ŋ), optionally chained with an
# apostrophe (straight ' or curly ’) followed by more letters. This is what
# lets "b'omu", "n'ekitabo", "Ng'enda" survive as ONE token instead of being
# treated as separate words + stray punctuation.
#
# NOTE: requires AT LEAST ONE apostrophe-group ('+' not '*'). See
# tests/test_tokenizer_deep.py case 05 — using '*' here meant every plain
# word (no apostrophe at all) got needlessly routed through the placeholder
# masking system, which hid known abbreviations like "Dr" from NLTK's own
# abbreviation list and broke "Dr." -> caused it to split into "Dr" + ".".
_LUGANDA_WORD_RE = r"[A-Za-zŋŊ]+(?:['’][A-Za-zŋŊ]+)+"

# Rule 7 — known abbreviations (word + trailing period kept as ONE unit).
# Extend this set as the team finds more real examples in the corpus.
# Word boundary (\b) on the left prevents matching inside a longer word
# (e.g. won't match "St" inside "Nsteesa").
_ABBREVIATIONS = {"Dr", "Mr", "Mrs", "Ms", "Prof", "St", "Rev", "Gen", "Sgt"}
_ABBREV_RE = r"\b(?:" + "|".join(re.escape(a) for a in _ABBREVIATIONS) + r")\."

# Combined regex: try the abbreviation pattern first at each position, so
# "Dr." is captured whole (word + period) before the plain word rule would
# otherwise grab just "Dr" and leave a lone trailing period behind.
_PROTECTED_RE = re.compile(rf"{_ABBREV_RE}|{_LUGANDA_WORD_RE}")

# Base placeholder tag used to shield matched words from NLTK. Deliberately
# alphanumeric-only so Treebank's tokenizer has nothing in it to split on.
# This is only a STARTING POINT now — see Rule 8. The actual tag used for
# any given call to tokenize() is derived from this base plus a random
# per-call suffix, so a fixed constant is never sent through NLTK.
_PLACEHOLDER_BASE_TAG = "XLGWRDX"


def _make_session_tag(text: str) -> str:
    """
    Rule 8 — collision-proof placeholder tag.

    A fixed placeholder tag (just "XLGWRDX" + a sequential integer) means
    any input text that happens to already contain that exact shape — a
    product code, a ticket ID, or literally the string "XLGWRDX0" — could
    either crash the restore step with KeyError (if that index was never
    actually generated this call) or, worse, silently get swapped for an
    unrelated word if the index DID coincide with a real placeholder.

    This generates a random per-call suffix and verifies it does not
    already appear anywhere in the source text before using it, retrying
    with a new random suffix on the rare chance of a collision. This
    makes an accidental (or adversarial) collision impossible for a given
    call, rather than merely "unlikely."

    Args:
        text: the raw input text this tokenize() call is processing.

    Returns:
        A placeholder tag prefix, guaranteed not to appear anywhere in
        `text`, safe to combine with a numeric suffix per placeholder.
    """
    tag = _PLACEHOLDER_BASE_TAG
    while tag in text:
        tag = f"{_PLACEHOLDER_BASE_TAG}{secrets.token_hex(4)}"
    return tag


def tokenize(
    text: Optional[str],
    lowercase: bool = False,
    normalize_apostrophe: bool = True,
) -> List[str]:
    """
    Tokenize Luganda text, correcting NLTK's handling of:
      - the curly apostrophe (’) in elision/ng' words,
      - known abbreviations (e.g. "Dr.") wrongly split from their period, and
      - placeholder/text namespace collisions (see Rule 8 above).

    Args:
        text: raw Luganda string. None or an empty/whitespace-only string
            returns an empty list rather than raising.
        lowercase: if True, lowercase tokens after tokenizing (off by
            default — Luganda capitalization carries information, e.g.
            sentence-initial "Ng'" vs mid-sentence "ng'").
        normalize_apostrophe: if True (default), curly ’ is normalized to
            straight ' inside protected words (Rule 2, below), so
            "b'omu" (straight) and "b'omu" (curly) collapse to the same
            token/vocabulary entry.

    Returns:
        list[str] of tokens, with elided/ng' words and abbreviations
        kept intact.
    """
    if not text or not text.strip():
        return []

    session_tag = _make_session_tag(text)
    placeholder_find_re = re.compile(rf"{re.escape(session_tag)}\d+")

    placeholders: Dict[str, str] = {}

    def _stash(match: "Match[str]") -> str:
        idx = len(placeholders)
        key = f"{session_tag}{idx}"
        word = match.group(0)
        if normalize_apostrophe:
            # Rule 2 — apostrophe canonicalization: curly ’ -> straight '
            word = word.replace("\u2019", "'")
        placeholders[key] = word
        return key

    # Rule 3 — mask-before-tokenize: protect fragile words/abbreviations
    # with placeholders BEFORE nltk ever sees them, instead of trying to
    # patch its output after the fact (unreliable once already shredded).
    protected_text = _PROTECTED_RE.sub(_stash, text)

    # Rule 4 — delegate everything else (commas, sentence-ending periods,
    # numbers, quotes around whole phrases) to NLTK, which already
    # handles it correctly.
    rough_tokens = _nltk_word_tokenize(protected_text)

    # Rule 5 — restore: swap placeholders back for the real, protected words.
    # Uses substring replacement (Rule 6) rather than exact-match, so a
    # placeholder that NLTK left glued to stray punctuation still resolves
    # correctly instead of leaking the raw placeholder string.
    def _restore(tok: str) -> str:
        return placeholder_find_re.sub(
            lambda m: placeholders[m.group(0)], tok
        )

    tokens = [_restore(tok) for tok in rough_tokens]

    if lowercase:
        tokens = [t.lower() for t in tokens]

    return tokens


def diagnose(sentence: str) -> Dict[str, object]:
    """
    Compare plain nltk.word_tokenize against tokenize() for one sentence.
    Useful for demonstrating/documenting exactly where and how the default
    tokenizer breaks.

    Args:
        sentence: a single sentence (or short text) to run through both
            the stock NLTK tokenizer and this module's tokenize().

    Returns:
        A dict with three keys:
            "sentence": the original input, unchanged.
            "nltk_default": list[str], output of plain nltk.word_tokenize.
            "custom_tokenize": list[str], output of this module's tokenize().
    """
    return {
        "sentence": sentence,
        "nltk_default": _nltk_word_tokenize(sentence),
        "custom_tokenize": tokenize(sentence),
    }