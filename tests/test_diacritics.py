"""
Tests for normalize_diacritics().

Two kinds of tests here on purpose:
1. Behavioral tests — confirm the function does what it currently should
   (a no-op, since CONFIRMED_VARIANTS is empty).
2. Guard-rail tests — assert that the PENDING_REVIEW candidate is NOT being
   merged. If someone adds an entry to CONFIRMED_VARIANTS without updating
   this test, that's a deliberate signal the reviewer needs to also update
   the guard-rail test, which forces a conscious decision rather than a
   silent slip.

Run with: pytest test_normalize_diacritics.py -v
"""

from normalizer.diacritics import (
    normalize_diacritics,
    list_pending_reviews,
    add_confirmed_variant,
    CONFIRMED_VARIANTS,
)


# --- current no-op behavior --------------------------------------------------

def test_confirmed_variants_currently_empty():
    """Sanity check: this test SHOULD fail the day someone adds a confirmed
    mapping — that's the point. It's a tripwire, not a bug.
    """
    assert CONFIRMED_VARIANTS == {}


def test_ng_apostrophe_form_untouched():
    raw = "ng'ekitongole kye yalimu kye kiri mu luwalo"
    assert normalize_diacritics(raw) == raw


def test_eng_letter_form_untouched():
    raw = "abaali bakuŋŋaanye"
    assert normalize_diacritics(raw) == raw


# --- guard-rail: pending candidate must stay unmerged -----------------------

def test_pending_variant_is_not_merged():
    """The ŋ vs ng' pair (log #9) is unresolved. Until a native speaker
    confirms it, both forms must independently round-trip unchanged and
    must NOT collapse to the same string.
    """
    eng_form = normalize_diacritics("bakuŋŋaanye")
    apostrophe_form = normalize_diacritics("ng'amulamusa")
    assert eng_form == "bakuŋŋaanye"
    assert apostrophe_form == "ng'amulamusa"


def test_pending_review_queue_contains_eng_variant():
    pending = list_pending_reviews()
    refs = [item["forms"] for item in pending]
    assert ["ŋŋ", "ng'"] in refs


# --- workflow test: how a confirmed mapping gets added later ----------------

def test_add_confirmed_variant_workflow():
    """Demonstrates the intended path once a native speaker confirms a pair
    — using a hypothetical example, not the real pending ŋ/ng' case, so this
    test doesn't accidentally document an unverified merge as 'correct'.
    """
    add_confirmed_variant("qq_test_variant", "qq_test_canonical", log_ref="test-only")
    result = normalize_diacritics("this has qq_test_variant in it")
    assert "qq_test_canonical" in result
    # cleanup so this test doesn't leak state into other tests
    del CONFIRMED_VARIANTS["qq_test_variant"]


def test_nfc_normalization_still_applied():
    """Even with no confirmed variants, Unicode NFC normalization should
    still run — this is an encoding fix, not a linguistic judgment call.
    """
    combining_form = "n\u0301"   # 'n' + combining acute accent
    precomposed_form = "\u0144"  # ń precomposed
    assert normalize_diacritics(combining_form) == normalize_diacritics(precomposed_form)