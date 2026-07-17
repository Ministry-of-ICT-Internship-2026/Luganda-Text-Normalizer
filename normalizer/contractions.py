"""
contractions.py – expands Luganda apostrophe-elisions before tokenization.

Luganda often drops a vowel and glues a short word onto the next one
with an apostrophe, e.g. 'n'emikyungwa' = 'na' + 'emikyungwa' ("and
jackfruit"). If left alone, the noun/verb strippers mistake the glued
letter for a class prefix and mangle both halves.

Only expand elisions we've explicitly confirmed — same safety
philosophy as FALSE_POSITIVES / CLOSED_CLASS elsewhere in this
project. Add more here as you confirm them; do not guess new ones in,
since an unconfirmed elision will silently corrupt text that wasn't
actually contracted.

ORDERING NOTE (fixed bug)
--------------------------
This module MUST run BEFORE tokenizer.tokenize(), not after and not on
already-tokenized output.

  * expand_elisions() operates on a raw string with regex + \\b word
    boundaries. Once tokenizer.tokenize() has already split/masked the
    text, "n'" is either its own token or merged inside a placeholder-
    protected span, and \\b no longer lines up with meaningful
    boundaries -- the pattern silently stops matching.
  * Running expansion first also means tokenizer.py never even sees a
    bare "n'" elision for the keys we've expanded here, so there's no
    double-handling / conflict with tokenizer's own apostrophe-word
    protection (which is intentionally left to handle the elisions we
    have NOT confirmed/expanded, e.g. "b'omu", "Ng'enda", "by'obulamu").

Use pipeline.process(text) rather than calling these two functions
separately in the wrong order.

CASE-PRESERVATION NOTE (fixed bug)
------------------------------------
The elision key is matched case-insensitively (so sentence-initial
"N'ekitabo" is recognized, not just lowercase "n'ekitabo"), but the
original code always substituted the lowercase expansion ('na'),
which silently lowercased sentence-initial words and could corrupt
downstream sentence-boundary detection that relies on capitalization.
Expansion now mirrors the case of the matched key: "n'" -> "na ",
"N'" -> "Na ".
"""

import re

# confirmed elision -> full word it stands for (lowercase canonical form)
ELISIONS = {
    'n': 'na',   # n'emikyungwa -> na emikyungwa ("and jackfruit")
}

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in ELISIONS) + r")(['\u2019])(?=\w)",
    re.IGNORECASE,
)


def _match_case(expansion: str, original_key: str) -> str:
    """Mirror the capitalization of original_key onto expansion.

    DOCUMENTED LIMITATION: our elision keys are single characters (e.g.
    'n'/'N'), so "capitalized" and "ALL CAPS" are indistinguishable from
    the key alone -- a single uppercase letter satisfies both
    `.isupper()` and `[0].isupper()`. We deliberately only ever
    capitalize the first letter of the expansion (never full-upper it),
    since a sentence-initial elision ("N'ekitabo" -> "Na ekitabo") is
    the overwhelmingly common real case; an elision inside an ALL-CAPS
    sentence ("NDDA N'EBINTU" -> "NDDA Na EBINTU") is comparatively rare
    and, if it matters to a caller, needs surrounding-context detection
    that is out of scope for this single-token heuristic.
    """
    if original_key[0].isupper():
        return expansion[0].upper() + expansion[1:]
    return expansion


def expand_elisions(text: str) -> str:
    """
    Split known apostrophe-contractions into two separate words.

    Handles both the straight apostrophe (') and the curly/typographic
    apostrophe (\u2019), since both appear in real-world Luganda text
    (see tokenizer.py's module docstring for why the curly quote is
    common — autocorrect on phones/Word/Docs).

    Preserves the case of the original elision key (Rule: case
    preservation, see module docstring) so sentence-initial "N'..."
    stays capitalized as "Na ..." rather than being silently
    lowercased.

    Example:
        "n'emikyungwa" -> "na emikyungwa"
        "N'ekitabo"    -> "Na ekitabo"
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        base = ELISIONS[key.lower()]
        return _match_case(base, key) + " "

    return _PATTERN.sub(_replace, text)