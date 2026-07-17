"""Tests for currency.py.

Run with: pytest test_currency.py -v
(or just: python test_currency.py -- it also runs standalone)
"""

import sys

sys.path.insert(0, ".")

from normalizer.currency import (
    find_currency_entities,
    normalize_currency_format,
    amount_to_words,
    expand_currency_to_words,
)


# ---------------------------------------------------------------------------
# Detection matrix (every format the module's own docstring claims to support)
# ---------------------------------------------------------------------------

def test_detect_slash_notation():
    ents = find_currency_entities("cost is 50,000/= only")
    assert len(ents) == 1 and ents[0]["code"] == "UGX" and ents[0]["amount"] == "50,000"


def test_detect_prefix_ugx_spaced():
    ents = find_currency_entities("UGX 50,000 for the room")
    assert len(ents) == 1 and ents[0]["code"] == "UGX"


def test_detect_prefix_ugx_no_space_mixed_case():
    ents = find_currency_entities("Ugx50,000 for the room")
    assert len(ents) == 1 and ents[0]["code"] == "UGX"


def test_detect_prefix_ush():
    ents = find_currency_entities("USh 50,000 for the room")
    assert len(ents) == 1 and ents[0]["code"] == "UGX"


def test_detect_prefix_shs():
    # "Shs" was listed nowhere in the old regex despite being in
    # _UGX_MARKERS -- now wired up and detectable.
    ents = find_currency_entities("Shs 50,000 for the room")
    assert len(ents) == 1 and ents[0]["code"] == "UGX"


def test_detect_suffix_ungrouped_digits_regression():
    # BUG in the original: the amount regex only accepted \d{1,3} or
    # proper comma groups, so a bare "50000" (this module's own
    # documented example) matched nothing at all.
    ents = find_currency_entities("cost is 50000 UGX today")
    assert len(ents) == 1, "ungrouped-digit amount should be detected"
    assert ents[0]["code"] == "UGX"
    assert ents[0]["amount"] == "50000"


def test_detect_suffix_grouped():
    ents = find_currency_entities("cost is 50,000 UGX today")
    assert len(ents) == 1 and ents[0]["amount"] == "50,000"


def test_detect_dollar_symbol():
    ents = find_currency_entities("price is $10 flat")
    assert len(ents) == 1 and ents[0]["code"] == "USD" and ents[0]["amount"] == "10"


def test_detect_usd_prefix():
    ents = find_currency_entities("price is USD 10 flat")
    assert len(ents) == 1 and ents[0]["code"] == "USD"


def test_detect_usd_suffix():
    ents = find_currency_entities("price is 10 USD flat")
    assert len(ents) == 1 and ents[0]["code"] == "USD"


def test_case_insensitivity_not_enumerated():
    # Old regex enumerated exact casings (UGX|Ugx|ugx); "UgX" fell
    # through the cracks. Now handled generically via re.IGNORECASE.
    ents = find_currency_entities("UgX 50,000 for the room")
    assert len(ents) == 1 and ents[0]["code"] == "UGX"


# ---------------------------------------------------------------------------
# Overlap-corruption regression (the "UGX UGX 50,000" bug)
# ---------------------------------------------------------------------------

def test_no_duplicate_marker_when_prefix_and_suffix_both_match():
    text = "cost is UGX 50,000/= today"
    out = normalize_currency_format(text)
    assert out.count("UGX") == 1, f"marker duplicated: {out!r}"
    assert out == "cost is UGX 50,000 today"


def test_no_duplicate_marker_dollar_and_usd_suffix():
    text = "price is $10 USD flat"
    out = normalize_currency_format(text)
    assert out.count("USD") == 1, f"marker duplicated: {out!r}"


def test_entities_do_not_overlap():
    text = "cost is UGX 50,000/= today, and also $10 USD flat"
    ents = find_currency_entities(text)
    for a, b in zip(ents, ents[1:]):
        assert a["span"][1] <= b["span"][0], f"overlapping entities: {a}, {b}"


# ---------------------------------------------------------------------------
# normalize_currency_format
# ---------------------------------------------------------------------------

def test_normalize_basic_forms():
    assert normalize_currency_format("50,000/=") == "UGX 50,000"
    assert normalize_currency_format("Ugx50,000") == "UGX 50,000"
    assert normalize_currency_format("$10") == "USD 10"
    assert normalize_currency_format("50000 UGX") == "UGX 50000"


def test_normalize_leaves_unrecognized_untouched():
    text = "just a number 12345 with no currency marker"
    assert normalize_currency_format(text) == text


def test_normalize_multiple_amounts_in_one_text():
    text = "Room A costs UGX 50,000 and Room B costs $10."
    out = normalize_currency_format(text)
    assert "UGX 50,000" in out and "USD 10" in out


# ---------------------------------------------------------------------------
# amount_to_words
# ---------------------------------------------------------------------------

def test_amount_to_words_basic():
    out = amount_to_words("10", "UGX")
    assert out.startswith("ssente za Uganda")
    assert "kkumi" in out  # stub's word for ten


def test_amount_to_words_unknown_code_raises():
    try:
        amount_to_words("10", "KES")
        assert False, "should have raised"
    except ValueError:
        pass


def test_amount_to_words_decimal_falls_back():
    out = amount_to_words("50,000.25", "UGX")
    assert out == "ssente za Uganda 50,000.25"


def test_amount_to_words_too_large_falls_back():
    out = amount_to_words("5,000,000,000", "UGX")
    assert out == "ssente za Uganda 5,000,000,000"


# ---------------------------------------------------------------------------
# expand_currency_to_words
# ---------------------------------------------------------------------------

def test_expand_currency_to_words_basic():
    out = expand_currency_to_words("Room costs UGX 10 per night.")
    assert "ssente za Uganda" in out
    assert "UGX" not in out


def test_expand_currency_to_words_no_currency_present():
    text = "no money mentioned here"
    assert expand_currency_to_words(text) == text


def test_expand_currency_to_words_multiple():
    out = expand_currency_to_words("UGX 10 or $10, your choice.")
    assert out.count("ssente za Uganda") == 1
    assert out.count("ddoola") == 1


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