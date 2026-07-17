"""
currency.py -- detects and normalizes currency amounts (UGX, USD, ...)
in Luganda/English-mixed text, and can spell amounts out as words.

Conceptually related to edge_cases.CURRENCY_RE (which protects
comma-grouped numbers elsewhere in the pipeline so other rules don't
corrupt them), but this module owns its own amount pattern rather than
importing that one, since it needs richer per-match metadata (marker,
currency code, span) than a plain detection regex provides. If
edge_cases.CURRENCY_RE's grouping rules ever change, re-check this
module's _AMOUNT pattern for drift -- the two are not wired together.

Real-world formats this module confirms handling of (see
tests/test_currency.py for the full matrix):
    50,000/=            (Ugandan "slash" notation)
    UGX 50,000
    Ugx50,000
    USh 50,000
    Shs 50,000
    50000 UGX            (ungrouped digits, no thousands commas)
    50,000 UGX
    $10  /  USD 10  /  10 USD

DESIGN PRINCIPLE: normalize the *symbol/marker* with confidence (that's
a closed, well-known set for UGX/USD); only spell the *amount* out into
words when explicitly asked (`words=True`), and reuse numbers.py rather
than reimplementing numeral logic here.

DOCUMENTED LIMITATION: the Luganda words used for the currency units
themselves -- "ssente" (money/coins, used generically for shillings)
and "ddoola" (the standard loanword for "dollar") -- are common,
everyday loanword usage, not a legally-defined terminology standard.
Other currencies (KES, TZS, EUR, GBP, ...) are intentionally NOT
covered yet; add them only with a confirmed symbol/word pair rather
than guessing by analogy.

DOCUMENTED LIMITATION: bare "sh" and dotted "u.sh" are deliberately
NOT recognized as markers, even though they show up in
_CANONICAL_CODE_BY_MARKER for completeness. Both are too ambiguous to
auto-detect safely: "sh" collides with ordinary short tokens/
abbreviations, and "u.sh" collides with sentence-initial abbreviation
patterns. If you need them, gate detection on stronger surrounding
context rather than adding them to the marker regex blindly.
"""

from __future__ import annotations

import re

from normalizer.number_words import NumberTooLargeError, number_to_words

__all__ = [
    "CURRENCY_WORDS",
    "find_currency_entities",
    "normalize_currency_format",
    "amount_to_words",
    "expand_currency_to_words",
]

# Canonical currency code -> Luganda unit word (see docstring limitation).
CURRENCY_WORDS = {
    "UGX": "ssente za Uganda",
    "USD": "ddoola",
}

# ---------------------------------------------------------------------------
# Single source of truth for markers.
#
# Previously the regex alternation (which markers are *detected*) and
# _UGX_MARKERS/_USD_MARKERS (which markers are *classified*) were two
# separate hand-maintained lists that had drifted out of sync: "Shs"/
# "sh"/"u.sh" were classifiable but never actually matchable, since
# they weren't in the regex. Building both the regex and the
# classification lookup from one dict makes that drift impossible.
#
# re.IGNORECASE is used at compile time (see below) instead of
# enumerating every casing (UGX|Ugx|ugx|...), which also fixes a real
# gap: the old regex would silently miss oddities like "UgX".
# ---------------------------------------------------------------------------

_PREFIX_WORD_MARKERS = {
    "ugx": "UGX", "ush": "UGX", "shs": "UGX",
    "usd": "USD", "us$": "USD",
}
_SUFFIX_WORD_MARKERS = {
    "ugx": "UGX", "ush": "UGX", "shs": "UGX",
    "usd": "USD",
}
# Symbols are handled outside the word-marker alternation because they
# have different \b requirements ("$" and "/=" aren't word characters).
_PREFIX_SYMBOLS = {"$": "USD"}
_SUFFIX_SYMBOLS = {"/=": "UGX"}

# Flat lookup used by _canonical_code(); union of every table above.
_CANONICAL_CODE_BY_MARKER: dict[str, str] = {
    **_PREFIX_WORD_MARKERS,
    **_SUFFIX_WORD_MARKERS,
    **{k.lower(): v for k, v in _PREFIX_SYMBOLS.items()},
    **{k.lower(): v for k, v in _SUFFIX_SYMBOLS.items()},
    # Present for completeness / documentation of the ambiguity above;
    # intentionally never reachable through the detection regexes.
    "sh": "UGX",
    "u.sh": "UGX",
}


def _alternation(words: dict) -> str:
    # Longest-first so e.g. "ush" isn't cut short by a shorter overlapping
    # alternative (not currently an issue with these specific markers, but
    # cheap insurance against it becoming one as markers are added).
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


# Amount: either proper thousands-grouped digits ("50,000", "1,234,567")
# or a plain ungrouped digit run ("50000", "10"), each with an optional
# decimal tail. The original version only supported the comma-grouped
# form, so a plain "50000 UGX" -- one of this module's own documented
# examples -- silently failed to match at all.
_AMOUNT = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"

_PREFIX_RE = re.compile(
    rf"(?:\b(?P<marker>{_alternation(_PREFIX_WORD_MARKERS)})"
    rf"|(?P<symbol>{_alternation(_PREFIX_SYMBOLS)}))"
    rf"\s*(?P<amount>{_AMOUNT})\b",
    re.IGNORECASE,
)

_SUFFIX_RE = re.compile(
    rf"\b(?P<amount>{_AMOUNT})\s*"
    rf"(?:(?P<marker>{_alternation(_SUFFIX_WORD_MARKERS)})\b"
    rf"|(?P<symbol2>{_alternation(_SUFFIX_SYMBOLS)}))",
    re.IGNORECASE,
)


def _canonical_code(marker: str | None) -> str | None:
    if marker is None:
        return None
    return _CANONICAL_CODE_BY_MARKER.get(marker.strip().lower())


def _matched_marker(match: re.Match) -> str | None:
    """Pull whichever marker/symbol alternative actually matched (only one
    of the named groups is non-None for a given match)."""
    groups = match.groupdict()
    for key in ("marker", "symbol", "symbol2"):
        if groups.get(key):
            return groups[key]
    return None


def _raw_matches(text: str) -> list[dict]:
    found = []
    for regex in (_PREFIX_RE, _SUFFIX_RE):
        for match in regex.finditer(text):
            code = _canonical_code(_matched_marker(match))
            if code is None:
                continue
            found.append({
                "span": match.span(),
                "code": code,
                "amount": match.group("amount"),
            })
    return found


def _resolve_overlaps(entities: list[dict]) -> list[dict]:
    """Prefix- and suffix-style matches can legitimately overlap on the
    same amount, e.g. "UGX 50,000/=" matches both a leading "UGX"
    marker and a trailing "/=" marker for the same "50,000". Feeding
    both overlapping spans into a replace pass corrupts the text (was
    observed to turn "UGX 50,000/=" into "UGX UGX 50,000"). Merge
    overlapping matches into a single entity spanning their union,
    keeping the code/amount from whichever side is the longer, more
    specific match -- so the whole redundant "UGX ... /=" collapses
    cleanly to "UGX 50,000" instead of leaving a stray "/=" behind."""
    ordered = sorted(entities, key=lambda d: d["span"][0])
    resolved: list[dict] = []
    for entity in ordered:
        start, end = entity["span"]
        if resolved and start < resolved[-1]["span"][1]:
            prev = resolved[-1]
            prev_start, prev_end = prev["span"]
            winner = entity if (end - start) > (prev_end - prev_start) else prev
            resolved[-1] = {
                "span": (min(prev_start, start), max(prev_end, end)),
                "code": winner["code"],
                "amount": winner["amount"],
            }
            continue
        resolved.append(dict(entity))
    return resolved


def find_currency_entities(text: str) -> list[dict]:
    """Return every recognized currency amount in `text` as a list of
    dicts: {"span": (start, end), "code": "UGX"|"USD", "amount": "50,000"},
    sorted left-to-right with overlapping prefix/suffix matches already
    resolved down to one entity per amount.

    Callers (e.g. numbers.expand_numbers) can pass the "span" values in
    as skip_spans so plain cardinal-number expansion doesn't also touch
    text that's already been identified as a currency amount.
    """
    found = _resolve_overlaps(_raw_matches(text))
    found.sort(key=lambda d: d["span"][0])
    return found


def _apply_entities(text: str, entities: list[dict], render) -> str:
    """Shared replace pass used by both normalize_currency_format and
    expand_currency_to_words. Both used to run their own independent
    regex.sub() calls, which is exactly what let overlapping
    prefix/suffix matches corrupt the text (see _resolve_overlaps
    docstring). Routing both through find_currency_entities's
    already-deduplicated span list fixes that at the source."""
    if not entities:
        return text
    for entity in sorted(entities, key=lambda d: d["span"][0], reverse=True):
        start, end = entity["span"]
        text = text[:start] + render(entity) + text[end:]
    return text


def normalize_currency_format(text: str) -> str:
    """Rewrite every recognized currency amount to the canonical
    "<CODE> <amount>" form (e.g. "50,000/=" -> "UGX 50,000",
    "Ugx50,000" -> "UGX 50,000", "$10" -> "USD 10",
    "50000 UGX" -> "UGX 50000").

    Amounts / markers not recognized are left completely untouched.
    """
    entities = find_currency_entities(text)
    return _apply_entities(text, entities, lambda e: f"{e['code']} {e['amount']}")


def amount_to_words(amount: str, code: str) -> str:
    """Spell out a currency amount as Luganda words, e.g.
    amount_to_words("50,000", "UGX") -> "ssente za Uganda enkumi amakumi ataano".

    See numbers.number_to_words for how the numeral itself is built.
    Amounts at or beyond numbers.py's documented magnitude ceiling (see
    numbers.MAX_SUPPORTED), or amounts with a fractional/decimal part
    (cents aren't in scope here), fall back to "<unit word> <digits>"
    rather than raising -- currency text should never be left half
    mangled just because the numeral is out of range.
    """
    unit_word = CURRENCY_WORDS.get(code)
    if unit_word is None:
        raise ValueError(f"unknown currency code {code!r}; add it to CURRENCY_WORDS first")

    digits = amount.replace(",", "")
    try:
        value = int(digits) if "." not in digits else float(digits)
        if isinstance(value, float):
            # Cents/fractional amounts aren't in scope for number_to_words;
            # keep the numeral as-is rather than guessing a fractional form.
            return f"{unit_word} {amount}"
        words = number_to_words(value)
    except (NumberTooLargeError, ValueError):
        return f"{unit_word} {amount}"

    return f"{unit_word} {words}"


def expand_currency_to_words(text: str) -> str:
    """Find every recognized currency amount in `text` and replace it
    with its fully spelled-out Luganda form."""
    entities = find_currency_entities(text)
    return _apply_entities(
        text, entities, lambda e: amount_to_words(e["amount"], e["code"])
    )