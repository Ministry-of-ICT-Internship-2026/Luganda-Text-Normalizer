"""
numbers.py -- expands Arabic numerals into Luganda number words.

DESIGN PRINCIPLE (same philosophy as diacritics.py / contractions.py):
only implement magnitudes we can build correctly from well-attested,
textbook-standard Luganda numeral forms. Where the standard forms are
not confidently known (very large magnitudes), FAIL LOUDLY
(NumberTooLargeError) rather than silently emitting a guessed word --
a wrong number word is worse than an untouched digit string.

Luganda numeral system, quick reference
----------------------------------------
Units (0-9):
    0 zeero, 1 emu, 2 bbiri, 3 ssatu, 4 nnya, 5 ttaano,
    6 mukaaga, 7 musanvu, 8 munaana, 9 mwenda

Teens (11-19) use "kkumi na <unit>" ("ten and <unit>"):
    11 kkumi na emu, 12 kkumi na bbiri, ... 19 kkumi na mwenda
    (10 itself is just "kkumi")

Tens (20-90) are their own words, and a non-zero remainder is joined
with "mu" ("ten(s) plus <unit>"), NOT "na":
    20 amakumi abiri, 30 amakumi asatu, 40 amakumi ana,
    50 amakumi ataano, 60 nkaaga, 70 nsanvu, 80 kinaana, 90 kyenda
    22 -> amakumi abiri mu bbiri, 45 -> amakumi ana mu ttaano

Hundreds (100-900) follow the same "mu"-joining pattern once you have
a remainder:
    100 kikumi, 200 bikumi bbiri, ... 900 bikumi mwenda
    105 -> kikumi mu ttaano, 250 -> bikumi bbiri mu amakumi ataano

Thousands (1,000-999,000) likewise:
    1000 lukumi, 2000 enkumi bbiri, ... 999000 enkumi mwenda mu
    bikumi kyenda mu mwenda

DOCUMENTED LIMITATION
----------------------
Magnitudes at or above one million are NOT implemented. Luganda has
words for these (spellings and usage vary by source and register),
but this project has not had a native speaker confirm a single
canonical form -- guessing would risk shipping a wrong or
regionally-contested word as if it were settled. number_to_words()
raises NumberTooLargeError for |n| >= MAX_SUPPORTED so callers get an
explicit, catchable signal instead of silently wrong output.

HOW TO EXTEND once a form is confirmed: add a new
(value, singular_word, plural_prefix_word) tuple to MAGNITUDES,
*before* the 1000-entry, e.g.::

    MAGNITUDES = [
        (1_000_000, "<confirmed word>", "<confirmed plural prefix>"),
        (1000, "lukumi", "enkumi"),
        (100, "kikumi", "bikumi"),
    ]

MAX_SUPPORTED is derived automatically from the table (see below), and
the recursive spelling logic requires no other changes -- it was
written generically for exactly this reason.
"""

from __future__ import annotations

import re
import warnings

__all__ = [
    "NumberTooLargeError",
    "number_to_words",
    "expand_numbers",
    "MAX_SUPPORTED",
]

UNITS = {
    0: "zeero", 1: "emu", 2: "bbiri", 3: "ssatu", 4: "nnya", 5: "ttaano",
    6: "mukaaga", 7: "musanvu", 8: "munaana", 9: "mwenda",
}

TENS = {
    10: "kkumi", 20: "amakumi abiri", 30: "amakumi asatu", 40: "amakumi ana",
    50: "amakumi ataano", 60: "nkaaga", 70: "nsanvu", 80: "kinaana", 90: "kyenda",
}

# (value, singular_word, plural_prefix_word) -- ordered LARGEST first.
# Plural is built as "<plural_prefix_word> <count spelled out>", e.g.
# bikumi bbiri (200), enkumi bbiri (2000). See module docstring
# "HOW TO EXTEND" for adding a confirmed 1,000,000+ word later.
MAGNITUDES: list[tuple[int, str, str]] = [
    (1000, "lukumi", "enkumi"),  # thousands
    (100, "kikumi", "bikumi"),   # hundreds
]

# Exclusive upper bound on |n|, derived from the largest magnitude in
# the table rather than hardcoded, so extending MAGNITUDES (see
# "HOW TO EXTEND" above) automatically raises this too.
MAX_SUPPORTED = MAGNITUDES[0][0] * 1000


class NumberTooLargeError(ValueError):
    """Raised when asked to spell out a magnitude this module does not yet
    have a native-speaker-confirmed word for (see module docstring)."""


def _below_20(n: int) -> str:
    if n < 10:
        return UNITS[n]
    if n == 10:
        return TENS[10]
    return f"{TENS[10]} na {UNITS[n - 10]}"


def _below_100(n: int) -> str:
    if n < 20:
        return _below_20(n)
    tens, rem = (n // 10) * 10, n % 10
    word = TENS[tens]
    if rem == 0:
        return word
    return f"{word} mu {UNITS[rem]}"


def _spell_grouped(n: int, magnitudes: list[tuple[int, str, str]]) -> str:
    """Recursively spell out n using a largest-first magnitude table.

    Once the table is exhausted (or n is smaller than every remaining
    magnitude), falls back to _below_100. This single recursive shape
    handles hundreds, thousands, and -- once MAGNITUDES is extended --
    any further magnitude, without needing a dedicated function per
    magnitude the way the original _below_1000 / _below_1_000_000
    pair did.
    """
    if not magnitudes:
        return _below_100(n)
    value, singular, plural_prefix = magnitudes[0]
    if n < value:
        return _spell_grouped(n, magnitudes[1:])
    count, remainder = divmod(n, value)
    if count == 1:
        count_word = singular
    else:
        count_word = f"{plural_prefix} {_spell_grouped(count, magnitudes[1:])}"
    if remainder == 0:
        return count_word
    return f"{count_word} mu {_spell_grouped(remainder, magnitudes)}"


def number_to_words(n: int) -> str:
    """Spell out an integer as Luganda number words.

    Args:
        n: any integer, positive, negative, or zero.

    Returns:
        The Luganda number-word phrase. Negative numbers are rendered
        as the English loanword "negative" followed by the Luganda
        words for the absolute value (e.g. -5 -> "negative ttaano").
        DOCUMENTED LIMITATION: no native-speaker-confirmed dedicated
        Luganda negation word for numerals has been vetted for this
        project, so we deliberately use the unambiguous borrowed
        marker rather than guessing one.

    Raises:
        TypeError: if n is not an int (bool is rejected too, since
            True/False are technically ints in Python but are never a
            legitimate caller intent here).
        NumberTooLargeError: if abs(n) >= MAX_SUPPORTED (see module
            docstring).
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"number_to_words expects an int, got {type(n).__name__}")
    if abs(n) >= MAX_SUPPORTED:
        raise NumberTooLargeError(
            f"number_to_words does not support |n| >= {MAX_SUPPORTED:,} "
            "(no confirmed Luganda word for this magnitude yet -- see "
            "module docstring)."
        )
    if n < 0:
        return f"negative {_spell_grouped(-n, MAGNITUDES)}"
    return _spell_grouped(n, MAGNITUDES)


# Matches a standalone integer (optionally negative) while explicitly
# refusing to match:
#   - digits glued to letters on either side, e.g. the "58" inside
#     "abaana58" or the "9" inside "9am" -- guarded by (?<!\w)/(?!\w).
#     This is a *backstop*: edge_cases.py is still expected to hand in
#     skip_spans for things like "9am" so they get their own, more
#     specific handling; this regex just means expand_numbers no
#     longer corrupts such tokens even if a caller forgets to pass
#     skip_spans.
#   - either half of a decimal number, e.g. "3.14" -- guarded by
#     (?<!\.) and (?!\.\d). Luganda decimal-fraction phrasing isn't
#     implemented, so we leave the whole number untouched rather than
#     mangling just the integer or fractional part.
#   - a "-" that is actually a range/score separator rather than a
#     minus sign, e.g. the "-15" in "10-15" -- guarded by (?<!\w)
#     before the optional "-", since a real negative sign is never
#     immediately preceded by another digit.
_NUMBER_RE = re.compile(r"(?<!\w)(?<!\.)-?\d+(?!\.\d)(?!\w)")


def expand_numbers(
    text: str,
    skip_spans: list[tuple[int, int]] | None = None,
    warn: bool = False,
) -> str:
    """Replace every standalone integer in `text` with its Luganda words.

    Args:
        text: input string.
        skip_spans: optional list of (start, end) character offsets into
            `text` to leave untouched (e.g. phone numbers or currency
            amounts already identified by edge_cases.find_numeric_entities
            / currency.find_currency_entities -- those have their own,
            more specific expansion and should not be double-processed
            here).
        warn: if True, emit a UserWarning (via the warnings module) for
            every number left untouched because it was too large for
            number_to_words. Off by default to keep normal pipeline runs
            quiet; useful when auditing a corpus for numbers that need a
            confirmed word added to MAGNITUDES.

    Numbers this module deliberately does NOT touch (left as digits,
    consistent with the "preserve rather than guess" project ethos):
        - numbers immediately glued to letters, e.g. "4G", "9am",
          "abaana58" -- see _NUMBER_RE docstring above.
        - numbers that are part of a decimal, e.g. "3.14" (both the
          "3" and the "14" are left alone, since Luganda decimal
          phrasing isn't implemented).
        - the second half of a hyphenated range/score, e.g. the "15"
          in "10-15", is spelled normally, but the "-" itself is
          preserved rather than read as a minus sign.
        - numbers too large for this module (raises are caught per-match
          and the original digit string is left in place, with no crash;
          pass warn=True to be notified when this happens).
    """
    skip_spans = skip_spans or []

    def _in_skip(start: int, end: int) -> bool:
        return any(s <= start and end <= e for s, e in skip_spans)

    def _replace(match: re.Match) -> str:
        start, end = match.span()
        if _in_skip(start, end):
            return match.group(0)
        try:
            return number_to_words(int(match.group(0)))
        except NumberTooLargeError:
            if warn:
                warnings.warn(
                    f"expand_numbers: left {match.group(0)!r} at "
                    f"[{start}:{end}] untouched -- too large for "
                    "number_to_words (see MAX_SUPPORTED).",
                    stacklevel=2,
                )
            return match.group(0)

    return _NUMBER_RE.sub(_replace, text)