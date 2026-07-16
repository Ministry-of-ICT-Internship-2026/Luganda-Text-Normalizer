"""
datetime_expand.py -- expands numeric dates and clock times into Luganda
words.

DESIGN PRINCIPLE (same as everywhere else in this project): only expand
patterns we can map to well-attested, standard Luganda vocabulary, and
document every simplifying assumption instead of silently baking it in.

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
"""

from __future__ import annotations

import re
from datetime import date

from .numbers import number_to_words

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

_PERIODS = [
    (6, 12, "ez'oku makya"),     # morning
    (12, 18, "ez'omu ttuntu"),   # afternoon
    (18, 21, "ez'olweggulo"),    # evening
    (21, 24, "ez'ekiro"),        # night
    (0, 6, "ez'ekiro"),          # night (wraps past midnight)
]


class DateExpandError(ValueError):
    """Raised when a date/time string can't be safely parsed. Callers
    should catch this and leave the original text untouched, same
    fallback philosophy as spelling.standardize_spelling."""


def _period_for_hour(hour: int) -> str:
    for start, end, label in _PERIODS:
        if start <= hour < end:
            return label
    return ""  # unreachable given the table above, but never raise on this


def weekday_name(d: date) -> str:
    """Return the Luganda name for the weekday of date `d`."""
    return WEEKDAYS[d.weekday()]


def month_name(month: int) -> str:
    """Return the Luganda name for month number 1-12."""
    if not 1 <= month <= 12:
        raise DateExpandError(f"month must be 1-12, got {month}")
    return MONTHS[month]


def date_to_words(day: int, month: int, year: int, include_weekday: bool = True) -> str:
    """Render a calendar date as Luganda words.

    The day-of-month and year are rendered as plain number words via
    numbers.number_to_words (this module does not attempt Luganda
    ordinal-number formation for "the Nth day" -- ordinals require
    noun-class agreement that hasn't been designed/vetted yet; see
    docs/architecture.md open questions).

    Example:
        date_to_words(16, 7, 2026) ->
            "Lwakutaano, olunaku 16 mu mwezi gwa Julaayi, mu mwaka 2026"
        (day-of-month and year numerals intentionally left as digits
        here for readability; pass through numbers.number_to_words
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

_DATE_DMY_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")
_DATE_YMD_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")


def expand_dates(text: str) -> str:
    """Find DD/MM/YYYY, DD-MM-YYYY, or YYYY-MM-DD dates in `text` and
    replace them with Luganda words. Dates that fail to parse (e.g.
    31/02/2026) are left untouched rather than raising, consistent with
    this project's "never crash or mangle unknown input" convention
    (see spelling.py)."""

    def _replace_dmy(match: re.Match) -> str:
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

    text = _DATE_YMD_RE.sub(_replace_ymd, text)
    text = _DATE_DMY_RE.sub(_replace_dmy, text)
    return text


def expand_times(text: str) -> str:
    """Find HH:MM clock times in `text` and replace them with Luganda
    "ssaawa" phrasing. Left untouched on any parse failure."""

    def _replace(match: re.Match) -> str:
        hour, minute = int(match.group(1)), int(match.group(2))
        try:
            return time_to_words(hour, minute)
        except DateExpandError:
            return match.group(0)

    return _TIME_RE.sub(_replace, text)


def expand_datetimes(text: str) -> str:
    """Convenience wrapper: expand dates, then times, in one pass."""
    text = expand_dates(text)
    text = expand_times(text)
    return text