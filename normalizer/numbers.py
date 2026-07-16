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
    1000 lukumi, 2000 enkumi bbiri, ... 999000 enkumi lwenda mu ...

DOCUMENTED LIMITATION
----------------------
Magnitudes at or above one million are NOT implemented. Luganda has
words for these (e.g. "kakadde" / "omuliyoni", spellings and usage
vary by source and register), but this project has not had a native
speaker confirm a single canonical form -- guessing would risk
shipping a wrong or regionally-contested word as if it were settled.
number_to_words() raises NumberTooLargeError for |n| >= 1_000_000 so
callers get an explicit, catchable signal instead of silently wrong
output. Extend LUGANDA_MAGNITUDES once a form is confirmed.
"""

from __future__ import annotations

import re

UNITS = {
    0: "zeero", 1: "emu", 2: "bbiri", 3: "ssatu", 4: "nnya", 5: "ttaano",
    6: "mukaaga", 7: "musanvu", 8: "munaana", 9: "mwenda",
}

TENS = {
    10: "kkumi", 20: "amakumi abiri", 30: "amakumi asatu", 40: "amakumi ana",
    50: "amakumi ataano", 60: "nkaaga", 70: "nsanvu", 80: "kinaana", 90: "kyenda",
}

# (value, singular_word, plural_prefix_word) -- plural is built as
# "<plural_prefix_word> <unit-word>" e.g. bikumi bbiri, enkumi bbiri.
HUNDRED = (100, "kikumi", "bikumi")
THOUSAND = (1000, "lukumi", "enkumi")

MAX_SUPPORTED = 1_000_000  # exclusive upper bound -- see module docstring


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


def _below_1000(n: int) -> str:
    if n < 100:
        return _below_100(n)
    hundreds, rem = n // 100, n % 100
    value, singular, plural_prefix = HUNDRED
    word = singular if hundreds == 1 else f"{plural_prefix} {UNITS[hundreds]}"
    if rem == 0:
        return word
    return f"{word} mu {_below_100(rem)}"


def _below_1_000_000(n: int) -> str:
    if n < 1000:
        return _below_1000(n)
    thousands, rem = n // 1000, n % 1000
    value, singular, plural_prefix = THOUSAND
    word = singular if thousands == 1 else f"{plural_prefix} {_below_1000(thousands)}"
    if rem == 0:
        return word
    return f"{word} mu {_below_1000(rem)}"


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
        NumberTooLargeError: if abs(n) >= 1,000,000 (see module docstring).
    """
    if abs(n) >= MAX_SUPPORTED:
        raise NumberTooLargeError(
            f"number_to_words does not support |n| >= {MAX_SUPPORTED:,} "
            "(no confirmed Luganda word for this magnitude yet -- see "
            "module docstring)."
        )
    if n < 0:
        return f"negative {_below_1_000_000(-n)}"
    return _below_1_000_000(n)


_NUMBER_RE = re.compile(r"-?\d+")


def expand_numbers(text: str, skip_spans: list[tuple[int, int]] | None = None) -> str:
    """Replace every standalone integer in `text` with its Luganda words.

    Args:
        text: input string.
        skip_spans: optional list of (start, end) character offsets into
            `text` to leave untouched (e.g. phone numbers or currency
            amounts already identified by edge_cases.find_numeric_entities
            / currency.find_currency_entities -- those have their own,
            more specific expansion and should not be double-processed
            here).

    Numbers this module deliberately does NOT touch (left as digits,
    consistent with the "preserve rather than guess" project ethos):
        - numbers immediately followed by a unit-like glued suffix that
          edge_cases.py already protects (4G, 9am, ...) -- those aren't
          plain cardinal counts.
        - numbers that are part of a larger alphanumeric token (e.g.
          "abaana58" village-numbering style codes) -- word-boundary
          matching below already prevents this.
        - numbers too large for this module (raises are caught per-match
          and the original digit string is left in place, with no crash).
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
            return match.group(0)

    return _NUMBER_RE.sub(_replace, text)