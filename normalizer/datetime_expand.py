"""
datetime_expand.py -- expands numeric dates and clock times into Luganda
words.

DESIGN PRINCIPLE (same as everywhere else in this project): only expand
patterns we can map to well-attested, standard Luganda vocabulary, and
document every simplifying assumption instead of silently baking it in.
Anything we are not confident about is left untouched rather than
guessed at, and every place we *are* guessing is called out explicitly
below so a native-speaker reviewer knows exactly what to check.

Weekday names (Lunaku lw'omu wiiki)
-------------------------------------
Sunday    Sande
Monday    Balaza
Tuesday   Lwakusatu
Wednesday Lwakuna
Thursday  Lwakutaano
Friday    Lwamukaaga
Saturday  Ssabbiiti

Month names (Myezi)
----------------------
These are the standard transliterated month names used in Luganda-
language print media, church calendars, and school materials:
Janwali, Febwali, Marisi, Apuli, Maayi, Juuni, Julaayi, Agusito,
Sebuttemba, Okitobba, Novemba, Desemba.

DOCUMENTED LIMITATION: real-world text (ministry documents, mixed
English/Luganda reports) sometimes spells these differently
("Julai" instead of "Julaayi", "Agosito" instead of "Agusito") or
simply uses the English month name. MONTH_ALIASES below maps a small,
clearly-marked set of such variants back to the canonical spelling so
they can still be recognised in free text. This alias list has NOT
been vetted by a native speaker/editor and should be treated as a
best-effort convenience, not an authoritative spelling list -- if in
doubt, add to it rather than trusting it blindly.

Clock time -- East African "6 o'clock" reckoning
-----------------------------------------------------
Like Swahili and other East African Bantu time systems, traditional
Luganda time-of-day counting starts the day at 6:00 (sunrise), not at
midnight: clock 7:00 is "ssaawa emu" (hour one), clock 13:00 is
"ssaawa musanvu" (hour seven), and so on, wrapping every 12 hours.

DOCUMENTED LIMITATION: the exact wording used for the morning/
afternoon/evening/night qualifier (e.g. "ez'oku makya" vs "ez'olweggulo")
depends on region and register, and the boundary hours between them
are not crisply fixed. This module attaches a qualifier using a
reasonable, commonly-used boundary split (06:00-11:59 morning,
12:00-17:59 afternoon, 18:00-20:59 evening, 21:00-05:59 night), but
that split has NOT been confirmed by a native speaker and should be
treated as a best-effort default, not a settled linguistic fact.
Callers needing precision should pass `include_period=False` and
supply their own qualifier.

KNOWN AMBIGUITIES (inherent, not something regex cleverness can fully
solve -- flagged here rather than silently guessed at):
  - A dotted number that happens to fall in-range, e.g. "1.2.2026" in
    a version string or build tag, is indistinguishable from a literal
    1 Feb 2026 date and WILL be expanded. If your text contains such
    identifiers, run expand_dates only over prose spans, not over
    identifiers/codes.
  - A colon-separated "H:MM" that is actually a ratio, sports score,
    or similar (e.g. "3:14") is indistinguishable from a time and WILL
    be expanded by expand_times. Same guidance: scope the call to
    prose text.

IDEMPOTENCY NOTE: expand_dates/expand_times/expand_datetimes are safe
to run more than once over the same text. Luganda output keeps the
day-of-month and year as plain digits by design (see date_to_words),
but those digits never again appear adjacent to a recognised
separator or month word, so none of the regexes below will re-match
already-expanded output.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from normalizer.number_words import number_to_words

__all__ = [
    "DateExpandError",
    "WEEKDAYS",
    "MONTHS",
    "MONTH_ALIASES",
    "weekday_name",
    "month_name",
    "month_number",
    "date_to_words",
    "time_to_words",
    "expand_dates",
    "expand_times",
    "expand_datetimes",
]


class DateExpandError(ValueError):
    """Raised when a date/time string can't be safely parsed. Callers
    should catch this and leave the original text untouched, same
    fallback philosophy as spelling.standardize_spelling."""


# ---------------------------------------------------------------------------
# Vocabulary tables
# ---------------------------------------------------------------------------

WEEKDAYS = {
    0: "Balaza",       # Python Monday=0
    1: "Lwakusatu",
    2: "Lwakuna",
    3: "Lwakutaano",
    4: "Lwamukaaga",
    5: "Ssabbiiti",
    6: "Sande",
}

MONTHS = {
    1: "Janwali", 2: "Febwali", 3: "Marisi", 4: "Apuli",
    5: "Maayi", 6: "Juuni", 7: "Julaayi", 8: "Agusito",
    9: "Sebuttemba", 10: "Okitobba", 11: "Novemba", 12: "Desemba",
}

# Reverse lookups, exposed for callers that need to detect/parse rather
# than generate (e.g. an upstream tokenizer checking "is this word
# already a month name?").
_WEEKDAY_NAME_TO_INDEX = {v.lower(): k for k, v in WEEKDAYS.items()}
_MONTH_NAME_TO_NUMBER = {v.lower(): k for k, v in MONTHS.items()}

# DOCUMENTED LIMITATION / best-effort, unvetted: alternate spellings and
# English equivalents, mapped to the canonical Luganda month number so
# free text using any of these still gets recognised and normalised to
# the canonical spelling in MONTHS. Keys are lowercase.
MONTH_ALIASES = {
    # English full names
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
    # English abbreviations
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    # Common alternate Luganda transliterations seen in the wild
    "julai": 7, "agosito": 8, "sebutemba": 9, "okitoba": 10,
}

_PERIODS = [
    (6, 12, "ez'oku makya"),     # morning
    (12, 18, "ez'omu ttuntu"),   # afternoon
    (18, 21, "ez'olweggulo"),    # evening
    (21, 24, "ez'ekiro"),        # night
    (0, 6, "ez'ekiro"),          # night (wraps past midnight)
]


def _period_for_hour(hour: int) -> str:
    for start, end, label in _PERIODS:
        if start <= hour < end:
            return label
    return ""  # unreachable given the table above, but never raise on this


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def weekday_name(d: date) -> str:
    """Return the Luganda name for the weekday of date `d`."""
    return WEEKDAYS[d.weekday()]


def month_name(month: int) -> str:
    """Return the Luganda name for month number 1-12."""
    if not 1 <= month <= 12:
        raise DateExpandError(f"month must be 1-12, got {month}")
    return MONTHS[month]


def month_number(word: str) -> Optional[int]:
    """Resolve a month word (canonical Luganda spelling, a known
    alternate spelling, or an English name/abbreviation) to its 1-12
    number. Case-insensitive. Returns None if unrecognised -- callers
    should treat that as "leave the text alone", not as an error."""
    key = word.strip().lower().rstrip(".")
    if key in _MONTH_NAME_TO_NUMBER:
        return _MONTH_NAME_TO_NUMBER[key]
    return MONTH_ALIASES.get(key)


def weekday_number(word: str) -> Optional[int]:
    """Resolve a Luganda weekday word to its Python weekday() index
    (Monday=0..Sunday=6). Case-insensitive. Returns None if
    unrecognised."""
    return _WEEKDAY_NAME_TO_INDEX.get(word.strip().lower())


# ---------------------------------------------------------------------------
# Core renderers
# ---------------------------------------------------------------------------

def date_to_words(day: int, month: int, year: int, include_weekday: bool = True) -> str:
    """Render a calendar date as Luganda words.

    The day-of-month and year are rendered as plain number words via
    number_words.number_to_words (this module does not attempt Luganda
    ordinal-number formation for "the Nth day" -- ordinals require
    noun-class agreement that hasn't been designed/vetted yet; see
    docs/architecture.md open questions).

    Example:
        date_to_words(16, 7, 2026) ->
            "Lwakutaano, olunaku 16 mu mwezi gwa Julaayi, mu mwaka 2026"
        (day-of-month and year numerals intentionally left as digits
        here for readability; pass through number_words.number_to_words
        yourself first if you need them fully spelled out.)
    """
    mon = month_name(month)
    try:
        d = date(year, month, day)
    except ValueError as exc:
        raise DateExpandError(f"invalid calendar date {year}-{month}-{day}: {exc}") from exc

    parts = []
    if include_weekday:
        parts.append(f"{weekday_name(d)},")
    parts.append(f"olunaku {day} mu mwezi gwa {mon}, mu mwaka {year}")
    return " ".join(parts)


def time_to_words(hour: int, minute: int = 0, include_period: bool = True) -> str:
    """Render a 24-hour clock time as Luganda "ssaawa" (hour-count) words,
    using the 6-o'clock-offset reckoning described in the module
    docstring.

    Example:
        time_to_words(7, 0)  -> "ssaawa emu ez'oku makya"
        time_to_words(19, 30) -> "ssaawa emu n'edakiika amakumi asatu ez'olweggulo"
    """
    if not (0 <= hour <= 23):
        raise DateExpandError(f"hour must be 0-23, got {hour}")
    if not (0 <= minute <= 59):
        raise DateExpandError(f"minute must be 0-59, got {minute}")

    # East African "6 o'clock" reckoning: 07:00 -> hour 1, 12:00 -> hour 6,
    # 18:00 -> hour 12, 00:00 -> hour 6, wrapping every 12 hours.
    luganda_hour = ((hour - 7) % 12) + 1

    phrase = f"ssaawa {number_to_words(luganda_hour)}"
    if minute:
        phrase += f" n'edakiika {number_to_words(minute)}"
    if include_period:
        period = _period_for_hour(hour)
        if period:
            phrase += f" {period}"
    return phrase


# ---------------------------------------------------------------------------
# Regex-driven expansion for free text
# ---------------------------------------------------------------------------

# Numeric dates. The separator is captured with a backreference (\2) so
# "16/07/2026" and "16-07-2026" match, but a mixed "16/07-2026" does not
# -- tightens the original version, which accepted any mix of '/' and
# '-' across the two separator positions.
_DATE_DMY_RE = re.compile(r"\b(\d{1,2})([/-])(\d{1,2})\2(\d{4})\b")

# Dot-separated dates are handled on their own, more conservative path:
# dotted numerics are also used for IP addresses, version strings, and
# decimals, so we lean on the day/month range check inside date_to_words
# (via DateExpandError -> leave untouched) to avoid mangling those.
_DATE_DMY_DOT_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")

_DATE_YMD_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")

_TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
_TIME_12H_RE = re.compile(
    r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*([AaPp])\.?[Mm]\.?\b"
)

_MONTH_WORD_PATTERN = "|".join(
    sorted(
        {re.escape(w) for w in list(MONTHS.values()) + list(MONTH_ALIASES.keys())},
        key=len,
        reverse=True,  # longest-first so "Sept" isn't eaten by a shorter alias
    )
)
# "16 July 2026" / "16 Julaayi, 2026"
_DATE_DAY_MONTHWORD_YEAR_RE = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_WORD_PATTERN})\.?,?\s+(\d{{4}})\b",
    re.IGNORECASE,
)
# "July 16, 2026" / "Julaayi 16 2026"
_DATE_MONTHWORD_DAY_YEAR_RE = re.compile(
    rf"\b({_MONTH_WORD_PATTERN})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b",
    re.IGNORECASE,
)


def _replace_dmy(match: re.Match) -> str:
    day, month, year = int(match.group(1)), int(match.group(3)), int(match.group(4))
    try:
        return date_to_words(day, month, year)
    except DateExpandError:
        return match.group(0)


def _replace_dmy_dot(match: re.Match) -> str:
    day, month, year = (int(g) for g in match.groups())
    try:
        return date_to_words(day, month, year)
    except DateExpandError:
        return match.group(0)


def _replace_ymd(match: re.Match) -> str:
    year, month, day = (int(g) for g in match.groups())
    try:
        return date_to_words(day, month, year)
    except DateExpandError:
        return match.group(0)


def _replace_day_monthword_year(match: re.Match) -> str:
    day, month_word, year = match.group(1), match.group(2), match.group(3)
    month = month_number(month_word)
    if month is None:
        return match.group(0)
    try:
        return date_to_words(int(day), month, int(year))
    except DateExpandError:
        return match.group(0)


def _replace_monthword_day_year(match: re.Match) -> str:
    month_word, day, year = match.group(1), match.group(2), match.group(3)
    month = month_number(month_word)
    if month is None:
        return match.group(0)
    try:
        return date_to_words(int(day), month, int(year))
    except DateExpandError:
        return match.group(0)


def expand_dates(text: str) -> str:
    """Find dates in `text` and replace them with Luganda words.
    Recognised forms:
      - ISO: YYYY-MM-DD
      - numeric: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
      - month-word: "16 July 2026", "July 16, 2026" (English or a
        recognised Luganda spelling/alias -- see MONTH_ALIASES)

    Dates that fail to parse (e.g. 31/02/2026) are left untouched
    rather than raising, consistent with this project's "never crash
    or mangle unknown input" convention (see spelling.py). Numeric
    DD/MM/YYYY is assumed throughout (not the US MM/DD/YYYY order),
    matching Ugandan convention.
    """
    text = _DATE_YMD_RE.sub(_replace_ymd, text)
    text = _DATE_DMY_RE.sub(_replace_dmy, text)
    text = _DATE_DMY_DOT_RE.sub(_replace_dmy_dot, text)
    text = _DATE_DAY_MONTHWORD_YEAR_RE.sub(_replace_day_monthword_year, text)
    text = _DATE_MONTHWORD_DAY_YEAR_RE.sub(_replace_monthword_day_year, text)
    return text


def _replace_12h(match: re.Match) -> str:
    hour12 = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    is_pm = match.group(3).lower() == "p"
    hour = (hour12 % 12) + (12 if is_pm else 0)
    try:
        return time_to_words(hour, minute)
    except DateExpandError:
        return match.group(0)


def _replace_24h(match: re.Match) -> str:
    hour, minute = int(match.group(1)), int(match.group(2))
    try:
        return time_to_words(hour, minute)
    except DateExpandError:
        return match.group(0)


def expand_times(text: str) -> str:
    """Find clock times in `text` and replace them with Luganda
    "ssaawa" phrasing. Recognised forms: 24-hour "HH:MM" and 12-hour
    "H:MM am/pm" (with or without minutes, with or without a space or
    dots in "a.m."/"p.m."). 12-hour forms are resolved first so a
    trailing "pm"/"am" isn't left dangling after the 24-hour regex
    consumes just the "H:MM" portion. Left untouched on any parse
    failure."""
    text = _TIME_12H_RE.sub(_replace_12h, text)
    text = _TIME_RE.sub(_replace_24h, text)
    return text


def expand_datetimes(text: str) -> str:
    """Convenience wrapper: expand dates, then times, in one pass."""
    text = expand_dates(text)
    text = expand_times(text)
    return text