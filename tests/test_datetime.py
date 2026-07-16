# test_numbers.py
"""Tests for normalizer/numbers.py."""

import pytest

from normalizer.numbers import (
    number_to_words,
    expand_numbers,
    NumberTooLargeError,
    MAX_SUPPORTED,
)


class TestUnits:
    def test_zero(self):
        assert number_to_words(0) == "zeero"

    @pytest.mark.parametrize("n,word", [
        (1, "emu"), (2, "bbiri"), (3, "ssatu"), (4, "nnya"), (5, "ttaano"),
        (6, "mukaaga"), (7, "musanvu"), (8, "munaana"), (9, "mwenda"),
    ])
    def test_single_digits(self, n, word):
        assert number_to_words(n) == word


class TestTeens:
    def test_ten(self):
        assert number_to_words(10) == "kkumi"

    def test_eleven_uses_na(self):
        assert number_to_words(11) == "kkumi na emu"

    def test_nineteen(self):
        assert number_to_words(19) == "kkumi na mwenda"


class TestTens:
    @pytest.mark.parametrize("n,word", [
        (20, "amakumi abiri"), (30, "amakumi asatu"), (40, "amakumi ana"),
        (50, "amakumi ataano"), (60, "nkaaga"), (70, "nsanvu"),
        (80, "kinaana"), (90, "kyenda"),
    ])
    def test_exact_tens(self, n, word):
        assert number_to_words(n) == word

    def test_tens_plus_unit_uses_mu_not_na(self):
        assert number_to_words(22) == "amakumi abiri mu bbiri"
        assert number_to_words(45) == "amakumi ana mu ttaano"

    def test_ninety_nine(self):
        assert number_to_words(99) == "kyenda mu mwenda"


class TestHundreds:
    def test_exact_hundred(self):
        assert number_to_words(100) == "kikumi"

    def test_hundred_plus_remainder(self):
        assert number_to_words(105) == "kikumi mu ttaano"

    def test_multiple_hundreds(self):
        assert number_to_words(200) == "bikumi bbiri"

    def test_multiple_hundreds_plus_remainder(self):
        assert number_to_words(250) == "bikumi bbiri mu amakumi ataano"

    def test_hundred_plus_teen(self):
        assert number_to_words(112) == "kikumi mu kkumi na bbiri"


class TestThousands:
    def test_exact_thousand(self):
        assert number_to_words(1000) == "lukumi"

    def test_thousand_plus_remainder(self):
        assert number_to_words(1001) == "lukumi mu emu"

    def test_multiple_thousands(self):
        assert number_to_words(2000) == "enkumi bbiri"

    def test_compound_number(self):
        assert number_to_words(1234) == "lukumi mu bikumi bbiri mu amakumi asatu mu nnya"


class TestNegativeAndBoundary:
    def test_negative_number(self):
        assert number_to_words(-5) == "negative ttaano"

    def test_max_supported_boundary_raises(self):
        with pytest.raises(NumberTooLargeError):
            number_to_words(MAX_SUPPORTED)

    def test_just_under_boundary_does_not_raise(self):
        # Should not raise -- just confirm it returns a non-empty string.
        assert isinstance(number_to_words(MAX_SUPPORTED - 1), str)

    def test_large_negative_also_raises(self):
        with pytest.raises(NumberTooLargeError):
            number_to_words(-MAX_SUPPORTED)


class TestExpandNumbers:
    def test_expands_number_in_sentence(self):
        result = expand_numbers("Nina 25 ente.")
        assert result == "Nina amakumi abiri mu ttaano ente."

    def test_expands_multiple_numbers(self):
        result = expand_numbers("3 ne 4")
        assert result == "ssatu ne nnya"

    def test_leaves_non_numeric_text_untouched(self):
        assert expand_numbers("Abaana bazannya.") == "Abaana bazannya."

    def test_number_too_large_is_left_as_digits_not_crashed(self):
        text = f"Ssente {MAX_SUPPORTED} nnyo."
        result = expand_numbers(text)
        assert str(MAX_SUPPORTED) in result  # left untouched, no crash

    def test_skip_spans_are_respected(self):
        text = "Ring 12345 today"
        start = text.index("12345")
        end = start + len("12345")
        result = expand_numbers(text, skip_spans=[(start, end)])
        assert "12345" in result

    def test_empty_string(self):
        assert expand_numbers("") == ""