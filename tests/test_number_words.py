import warnings

import pytest

from number_words import (
    MAX_SUPPORTED,
    NumberTooLargeError,
    expand_numbers,
    number_to_words,
)


# ---------------------------------------------------------------------
# number_to_words: core correctness (values pulled straight from the
# module's own docstring examples, so these also guard against
# regressions from the _below_1000/_below_1_000_000 -> _spell_grouped
# refactor)
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "n, expected",
    [
        (0, "zeero"),
        (1, "emu"),
        (9, "mwenda"),
        (10, "kkumi"),
        (11, "kkumi na emu"),
        (19, "kkumi na mwenda"),
        (20, "amakumi abiri"),
        (22, "amakumi abiri mu bbiri"),
        (30, "amakumi asatu"),
        (45, "amakumi ana mu ttaano"),
        (60, "nkaaga"),
        (90, "kyenda"),
        (99, "kyenda mu mwenda"),
        (100, "kikumi"),
        (105, "kikumi mu ttaano"),
        (200, "bikumi bbiri"),
        (250, "bikumi bbiri mu amakumi ataano"),
        (900, "bikumi mwenda"),
        (999, "bikumi mwenda mu kyenda mu mwenda"),
        (1000, "lukumi"),
        (2000, "enkumi bbiri"),
        (1050, "lukumi mu amakumi ataano"),
        (10_000, "enkumi kkumi"),
        (999_999, "enkumi bikumi mwenda mu kyenda mu mwenda "
                  "mu bikumi mwenda mu kyenda mu mwenda"),
    ],
)
def test_number_to_words_examples(n, expected):
    assert number_to_words(n) == expected


def test_negative_numbers_use_english_loanword():
    assert number_to_words(-5) == "negative ttaano"
    assert number_to_words(-100) == "negative kikumi"


def test_zero_and_negative_zero_are_identical():
    assert number_to_words(0) == number_to_words(-0) == "zeero"


def test_boundary_just_under_max_supported_works():
    assert number_to_words(MAX_SUPPORTED - 1)  # doesn't raise


def test_boundary_at_max_supported_raises():
    with pytest.raises(NumberTooLargeError):
        number_to_words(MAX_SUPPORTED)


def test_boundary_negative_at_max_supported_raises():
    with pytest.raises(NumberTooLargeError):
        number_to_words(-MAX_SUPPORTED)


def test_non_int_raises_type_error():
    with pytest.raises(TypeError):
        number_to_words(3.14)
    with pytest.raises(TypeError):
        number_to_words("5")


def test_bool_raises_type_error():
    # bool is technically an int subclass in Python; explicitly rejected
    # since a caller passing True/False here is always a mistake.
    with pytest.raises(TypeError):
        number_to_words(True)


# ---------------------------------------------------------------------
# expand_numbers: plain replacement behavior
# ---------------------------------------------------------------------

def test_expand_numbers_basic_sentence():
    assert expand_numbers("Nina 5 abaana") == "Nina ttaano abaana"


def test_expand_numbers_multiple_numbers():
    assert expand_numbers("10 ne 20") == "kkumi ne amakumi abiri"


def test_expand_numbers_respects_skip_spans():
    text = "Ffowuni ye 0700123456"
    start = text.index("0700123456")
    end = start + len("0700123456")
    assert expand_numbers(text, skip_spans=[(start, end)]) == text


def test_expand_numbers_too_large_left_untouched_no_crash():
    text = f"{MAX_SUPPORTED} ne ebirala"
    result = expand_numbers(text)
    assert str(MAX_SUPPORTED) in result


def test_expand_numbers_warns_when_requested():
    text = str(MAX_SUPPORTED)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        expand_numbers(text, warn=True)
    assert any("too large" in str(w.message) for w in caught)


def test_expand_numbers_silent_by_default():
    text = str(MAX_SUPPORTED)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        expand_numbers(text)
    assert caught == []


# ---------------------------------------------------------------------
# Regression tests for bugs found in the original regex (r"-?\d+" with
# no boundary guards at all)
# ---------------------------------------------------------------------

def test_does_not_corrupt_digits_glued_to_letters():
    # Original regex matched the bare "58" here and replaced it,
    # producing "abaanaamakumi ataano mu munaana" -- garbage.
    assert expand_numbers("abaana58") == "abaana58"


def test_does_not_corrupt_time_suffix():
    # Original regex matched "9" and replaced it in-place, producing
    # "mwendaam" for "9am".
    assert expand_numbers("9am") == "9am"


def test_does_not_corrupt_unit_suffix():
    assert expand_numbers("4G") == "4G"


def test_range_hyphen_is_not_read_as_minus():
    # Original regex greedily matched "-15" as a negative number here,
    # producing "ttaano negative kkumi na ttaano" for a plain range.
    result = expand_numbers("10-15")
    assert "negative" not in result
    assert result == "kkumi-kkumi na ttaano"


def test_score_hyphen_is_not_read_as_minus():
    result = expand_numbers("emyezi 5-3")
    assert "negative" not in result


def test_genuine_negative_number_still_works():
    assert expand_numbers("obuwuka -5") == "obuwuka negative ttaano"


def test_negative_at_string_start_still_works():
    assert expand_numbers("-5 digrii") == "negative ttaano digrii"


def test_decimal_number_left_entirely_untouched():
    # Original regex spelled out "3" and "14" independently, mangling
    # the decimal. Decimal phrasing isn't implemented, so both halves
    # should be left as digits.
    assert expand_numbers("obuzito 3.14 kg") == "obuzito 3.14 kg"


def test_negative_decimal_left_entirely_untouched():
    assert expand_numbers("-3.14") == "-3.14"


def test_plain_integer_next_to_punctuation_still_expands():
    assert expand_numbers("bantu 5, embwa 2.") == "bantu ttaano, embwa bbiri."


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))