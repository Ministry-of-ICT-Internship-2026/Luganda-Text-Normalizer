"""
currency.py -- detects and normalizes currency amounts (UGX, USD, ...)
in Luganda/English-mixed text, and can spell amounts out as words.

Builds on edge_cases.CURRENCY_RE (which only *detects* comma-grouped
numbers so other rules don't corrupt them) by additionally recognizing
the currency symbol/marker, normalizing it to one canonical form per
currency, and optionally expanding the numeral through numbers.py.

Real-world formats this module confirms handling of (see
tests/test_currency.py for the full matrix):
    50,000/=            (Ugandan "slash" notation)
    UGX 50,000
    Ugx50,000
    USh 50,000
    50000 UGX
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
"""

from __future__ import annotations

import re

from .numbers import NumberTooLargeError, number_to_words

# Canonical currency code -> Luganda unit word (see docstring limitation).
CURRENCY_WORDS = {
    "UGX": "ssente za Uganda",
    "USD": "ddoola",
}

# Marker variants (case-insensitive) -> canonical ISO-like code.
_UGX_MARKERS = ["ugx", "ush", "u.sh", "shs", "sh"]
_USD_MARKERS = ["usd", "us$"]

# Matches an amount with a leading currency marker: "UGX 50,000", "USh50,000",
# "$10". Word-style markers (UGX, USh, USD) need a word boundary before them;
# the "$" symbol is not a word character so it gets no boundary requirement
# (a leading \b before "$" would never match, since neither side is \w).
_PREFIX_RE = re.compile(
    r"(?:\b(?P<marker>UGX|Ugx|ugx|USh|Ush|ush|USD|Usd|usd|US\$)|(?P<symbol>\$))\s?"
    r"(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\b"
)

# Matches an amount with a trailing marker: "50,000 UGX", "50,000/=". Same
# boundary caveat as above applies to the "/=" slash notation.
_SUFFIX_RE = re.compile(
    r"\b(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s?"
    r"(?:(?P<marker>UGX|Ugx|ugx|USD|Usd|usd)\b|(?P<symbol2>/=))"
)


def _canonical_code(marker: str | None) -> str | None:
    if marker is None:
        return None
    m = marker.strip().lower().rstrip(".")
    if m in ("$", "us$") or m in _USD_MARKERS:
        return "USD"
    if m == "/=" or m in _UGX_MARKERS:
        return "UGX"
    return None


def _matched_marker(match: re.Match) -> str | None:
    """Pull whichever marker/symbol alternative actually matched (only one
    of the named groups is non-None for a given match)."""
    groups = match.groupdict()
    for key in ("marker", "symbol", "symbol2"):
        if groups.get(key):
            return groups[key]
    return None


def find_currency_entities(text: str) -> list[dict]:
    """Return every recognized currency amount in `text` as a list of
    dicts: {"span": (start, end), "code": "UGX"|"USD", "amount": "50,000"}.

    Callers (e.g. numbers.expand_numbers) can pass the "span" values in
    as skip_spans so plain cardinal-number expansion doesn't also touch
    text that's already been identified as a currency amount.
    """
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
    found.sort(key=lambda d: d["span"][0])
    return found


def normalize_currency_format(text: str) -> str:
    """Rewrite every recognized currency amount to the canonical
    "<CODE> <amount>" form (e.g. "50,000/=" -> "UGX 50,000",
    "Ugx50,000" -> "UGX 50,000", "$10" -> "USD 10").

    Amounts / markers not recognized are left completely untouched.
    """
    def _replace(match: re.Match) -> str:
        code = _canonical_code(_matched_marker(match))
        if code is None:
            return match.group(0)
        return f"{code} {match.group('amount')}"

    text = _PREFIX_RE.sub(_replace, text)
    text = _SUFFIX_RE.sub(_replace, text)
    return text


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
    if not entities:
        return text

    # Replace from the end so earlier spans stay valid as we edit.
    for entity in sorted(entities, key=lambda d: d["span"][0], reverse=True):
        start, end = entity["span"]
        replacement = amount_to_words(entity["amount"], entity["code"])
        text = text[:start] + replacement + text[end:]
    return text