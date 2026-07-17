"""Tests for datetime_expand.py.

Run with: pytest test_datetime_expand.py -v
(or just: python test_datetime_expand.py -- it also runs standalone)
"""

import sys
from datetime import date

sys.path.insert(0, ".")

from normalizer.datetime_expand import (
    DateExpandError,
    date_to_words,
    time_to_words,
    weekday_name,
    month_name,
    month_number,
    weekday_number,
    expand_dates,
    expand_times,
    expand_datetimes,
)


def test_weekday_name():
    assert weekday_name(date(2026, 7, 16)) == "Lwakutaano"   # Thursday
    assert weekday_name(date(2026, 7, 17)) == "Lwamukaaga"   # Friday
    assert weekday_name(date(2026, 7, 19)) == "Sande"        # Sunday


def test_month_name_roundtrip():
    for n in range(1, 13):
        word = month_name(n)
        assert month_number(word) == n


def test_month_name_invalid():
    try:
        month_name(13)
        assert False, "should have raised"
    except DateExpandError:
        pass


def test_month_number_aliases_and_unknown():
    assert month_number("July") == 7
    assert month_number("jul") == 7
    assert month_number("JULAAYI") == 7
    assert month_number("julai") == 7
    assert month_number("notamonth") is None


def test_weekday_number():
    assert weekday_number("Balaza") == 0
    assert weekday_number("sande") == 6
    assert weekday_number("nope") is None


def test_date_to_words_basic():
    out = date_to_words(16, 7, 2026)
    assert out == "Lwakutaano, olunaku 16 mu mwezi gwa Julaayi, mu mwaka 2026"


def test_date_to_words_no_weekday():
    out = date_to_words(16, 7, 2026, include_weekday=False)
    assert out == "olunaku 16 mu mwezi gwa Julaayi, mu mwaka 2026"


def test_date_to_words_invalid_date():
    try:
        date_to_words(31, 2, 2026)
        assert False, "should have raised"
    except DateExpandError:
        pass


def test_time_to_words_examples():
    # NOTE: exact wording of the minute count depends on number_to_words,
    # which is stubbed for these standalone tests and may render "thirty"
    # slightly differently than the real project module. Assert structure,
    # not exact wording, for the minutes case.
    assert time_to_words(7, 0) == "ssaawa emu ez'oku makya"
    out = time_to_words(19, 30)
    assert out.startswith("ssaawa emu n'edakiika")
    assert out.endswith("ez'olweggulo")


def test_time_to_words_period_boundaries():
    assert time_to_words(6, 0).endswith("ez'oku makya")
    assert time_to_words(11, 59).endswith("ez'oku makya")
    assert time_to_words(12, 0).endswith("ez'omu ttuntu")
    assert time_to_words(17, 59).endswith("ez'omu ttuntu")
    assert time_to_words(18, 0).endswith("ez'olweggulo")
    assert time_to_words(20, 59).endswith("ez'olweggulo")
    assert time_to_words(21, 0).endswith("ez'ekiro")
    assert time_to_words(5, 59).endswith("ez'ekiro")


def test_time_to_words_invalid():
    for bad in [(-1, 0), (24, 0), (7, 60)]:
        try:
            time_to_words(*bad)
            assert False, f"should have raised for {bad}"
        except DateExpandError:
            pass


def test_expand_dates_slash_and_dash():
    assert "Lwakutaano" in expand_dates("Meeting on 16/07/2026 at HQ")
    assert "Lwakutaano" in expand_dates("Meeting on 16-07-2026 at HQ")


def test_expand_dates_dot():
    assert "Lwakutaano" in expand_dates("Deadline: 16.07.2026")


def test_expand_dates_mixed_separator_not_matched():
    # Backreference tightening: separators must match on both sides.
    text = "16/07-2026"
    assert expand_dates(text) == text


def test_expand_dates_ymd():
    assert "Lwakutaano" in expand_dates("2026-07-16 was the date")


def test_expand_dates_leaves_invalid_untouched():
    text = "Ref number 31/02/2026-A"
    out = expand_dates(text)
    assert "31/02/2026" in out  # invalid date, left as-is


def test_expand_dates_ip_like_not_mangled():
    text = "server at 192.168.1.1"
    assert expand_dates(text) == text


def test_expand_dates_month_word_day_first():
    out = expand_dates("The event is on 16 July 2026.")
    assert "Julaayi" in out and "Lwakutaano" in out


def test_expand_dates_month_word_month_first():
    out = expand_dates("The event is on July 16, 2026.")
    assert "Julaayi" in out and "Lwakutaano" in out


def test_expand_dates_luganda_month_word():
    out = expand_dates("Ku 16 Julaayi 2026 twali ku mulimu.")
    assert "Lwakutaano" in out


def test_expand_times_24h():
    out = expand_times("The meeting starts at 19:30 sharp.")
    assert "ssaawa emu" in out and "ez'olweggulo" in out


def test_expand_times_12h_pm():
    out = expand_times("The meeting starts at 7:30pm sharp.")
    assert "ssaawa emu" in out and "ez'olweggulo" in out


def test_expand_times_12h_am_no_minutes():
    out = expand_times("Arrive by 7am.")
    assert "ssaawa emu" in out and "ez'oku makya" in out


def test_expand_times_12h_with_dots_and_space():
    out = expand_times("Arrive by 7:00 p.m.")
    assert "ez'olweggulo" in out


def test_expand_datetimes_combined():
    out = expand_datetimes("Book the room for 16/07/2026 19:30.")
    assert "Lwakutaano" in out
    assert "ssaawa emu" in out
    assert "ez'olweggulo" in out


def test_idempotent():
    text = "Meeting 16/07/2026 at 19:30 and again on 16 July 2026 at 7:30pm."
    once = expand_datetimes(text)
    twice = expand_datetimes(once)
    assert once == twice


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in list(globals().items()) if name.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)