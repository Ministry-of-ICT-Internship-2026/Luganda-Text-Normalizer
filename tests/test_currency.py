# test_currency.py
"""Tests for normalizer/currency.py."""

import pytest

from normalizer.currency import (
    find_currency_entities,
    normalize_currency_format,
    amount_to_words,
    expand_currency_to_words,
)


class TestFindCurrencyEntities:
    def test_slash_notation(self):
        found = find_currency_entities("Ekiguzibwa 50,000/= nedda.")
        assert len(found) == 1
        assert found[0]["code"] == "UGX"
        assert found[0]["amount"] == "50,000"

    def test_ugx_prefix(self):
        found = find_currency_entities("UGX 50,000 nedda.")
        assert found[0]["code"] == "UGX"

    def test_ugx_glued_prefix(self):
        found = find_currency_entities("Ugx50,000 nedda.")
        assert found[0]["code"] == "UGX"
        assert found[0]["amount"] == "50,000"

    def test_dollar_symbol(self):
        found = find_currency_entities("Kiguzibwa $10 mu ssande.")
        assert found[0]["code"] == "USD"
        assert found[0]["amount"] == "10"

    def test_usd_suffix(self):
        found = find_currency_entities("10 USD nedda.")
        assert found[0]["code"] == "USD"

    def test_multiple_entities_sorted_by_position(self):
        found = find_currency_entities("UGX 1,000 ne USD 5.")
        assert len(found) == 2
        assert found[0]["code"] == "UGX"
        assert found[1]["code"] == "USD"

    def test_no_currency_present(self):
        assert find_currency_entities("Abaana bazannya.") == []

    def test_plain_number_without_marker_not_matched(self):
        # A bare comma-grouped number with no currency marker at all
        # should not be reported as a currency entity.
        assert find_currency_entities("Bantu 50,000 baali eyo.") == []


class TestNormalizeCurrencyFormat:
    def test_slash_notation_normalized(self):
        assert normalize_currency_format("50,000/= ssente") == "UGX 50,000 ssente"

    def test_glued_prefix_normalized(self):
        assert normalize_currency_format("Ugx50,000") == "UGX 50,000"

    def test_dollar_symbol_normalized(self):
        assert normalize_currency_format("$10") == "USD 10"

    def test_already_canonical_stays_same(self):
        assert normalize_currency_format("UGX 50,000") == "UGX 50,000"

    def test_untouched_when_no_currency(self):
        text = "Abaana bazannya nnyo."
        assert normalize_currency_format(text) == text


class TestAmountToWords:
    def test_simple_amount(self):
        assert amount_to_words("10", "USD") == "ddoola kkumi"

    def test_comma_grouped_amount(self):
        result = amount_to_words("50,000", "UGX")
        assert result == "ssente za Uganda enkumi amakumi ataano"

    def test_unknown_currency_code_raises(self):
        with pytest.raises(ValueError):
            amount_to_words("10", "EUR")

    def test_fractional_amount_falls_back_to_digits(self):
        result = amount_to_words("10.50", "USD")
        assert result == "ddoola 10.50"

    def test_too_large_amount_falls_back_to_digits(self):
        result = amount_to_words("2,000,000", "UGX")
        assert "2,000,000" in result
        assert result.startswith("ssente za Uganda")


class TestExpandCurrencyToWords:
    def test_expands_single_amount(self):
        result = expand_currency_to_words("Ekiguzibwa $10 nedda.")
        assert result == "Ekiguzibwa ddoola kkumi nedda."

    def test_expands_multiple_amounts_correctly(self):
        result = expand_currency_to_words("UGX 100 ne USD 5.")
        assert "ssente za Uganda kikumi" in result
        assert "ddoola ttaano" in result

    def test_no_currency_returns_unchanged(self):
        text = "Abaana bazannya nnyo."
        assert expand_currency_to_words(text) == text