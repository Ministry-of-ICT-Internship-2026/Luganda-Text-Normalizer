"""
Tests for edge_cases.py — mixed-language text, numbers, and emoji/symbols.

Where possible, tests use real examples from the corpus (the "stress" and
"Chef" code-switching found in twitter_source.txt). Number and emoji cases
use realistic but synthetic examples, since the original samples didn't
happen to contain phone numbers or emoji.

Run with: pytest test_edge_cases.py -v
"""

from normalizer.edge_cases import (
    fix_number_word_spacing,
    find_numeric_entities,
    extract_emoji,
    extract_hashtags_and_mentions,
    handle_social_edge_cases,
)
from normalizer.cleaner import clean_text


# --- 1. Mixed-language text: must survive untouched -------------------------

def test_english_word_stress_preserved_through_full_pipeline():
    raw = "Omusajja abadde ne stress z'awaka  avuze ennyonyi n'agitomeza"
    cleaned = clean_text(raw)
    assert "stress" in cleaned


def test_english_word_chef_preserved_through_full_pipeline():
    raw = "Kylie Jerna omukozi we akola nga Chef nga kati yavaayo"
    cleaned = clean_text(raw)
    assert "Chef" in cleaned


def test_letter_then_digit_left_untouched():
    # fix_number_word_spacing only targets digit-THEN-letter (like "58Baliraanwa").
    # A word ending in a digit (username, model number, etc.) should NOT be
    # split apart - "stress4" staying glued is correct, safe behavior.
    raw = "Yali stress4 ku mulimu"
    cleaned = fix_number_word_spacing(raw)
    assert "stress4" in cleaned


# --- 2. Numbers ---------------------------------------------------------------

def test_known_word_stuck_to_number_still_gets_spaced():
    # This is the original log #10 case — must not regress
    raw = "bulenzi. 58Baliraanwa be ne baganda be"
    cleaned = fix_number_word_spacing(raw)
    assert "58 Baliraanwa" in cleaned


def test_tech_abbreviation_4g_not_split():
    raw = "network ya 4G etandise mu Uganda"
    cleaned = fix_number_word_spacing(raw)
    assert "4G" in cleaned
    assert "4 G" not in cleaned


def test_tech_abbreviation_3d_not_split():
    raw = "ekifaananyi kya 3D"
    cleaned = fix_number_word_spacing(raw)
    assert "3D" in cleaned


def test_time_abbreviation_9am_not_split():
    raw = "olukungaana luli ku 9am"
    cleaned = fix_number_word_spacing(raw)
    assert "9am" in cleaned


def test_phone_number_detected():
    raw = "Ntuutte ku namba eno 0700123456 nga simanyi"
    entities = find_numeric_entities(raw)
    assert any("0700123456" in "".join(m) if isinstance(m, tuple) else m in raw
               for m in entities["phone_numbers"]) or entities["phone_numbers"]


def test_currency_amount_untouched_by_cleaning():
    raw = "Ssente ze yasasula 50,000/= zaali nnyingi"
    cleaned = clean_text(raw)
    assert "50,000/=" in cleaned


def test_currency_amount_detected():
    raw = "yagula ku 50,000/="
    entities = find_numeric_entities(raw)
    assert any(amt.startswith("50,000") for amt in entities["currency_amounts"])


# --- 3. Emoji / symbols --------------------------------------------------------

def test_emoji_stripped_by_default():
    raw = "Nsanyuse nnyo leero 😂🔥 twebaze"
    cleaned = clean_text(raw)
    assert "😂" not in cleaned
    assert "🔥" not in cleaned
    assert "Nsanyuse" in cleaned and "twebaze" in cleaned


def test_emoji_extraction_returns_found_list():
    raw = "Webale nnyo 🙏🙏"
    cleaned, found = extract_emoji(raw)
    assert "🙏" in found
    assert "🙏" not in cleaned


def test_emoji_can_be_preserved_when_opted_out():
    raw = "Nsanyuse nnyo 😂"
    cleaned = clean_text(raw, strip_emoji=False)
    assert "😂" in cleaned


def test_no_emoji_is_a_safe_no_op():
    raw = "Kino kigambo kya Luganda ekitalimu mu mmwaanyi gyonna"
    cleaned, found = extract_emoji(raw)
    assert found == []
    assert cleaned.strip() == raw.strip()


def test_hashtags_preserved_by_default():
    raw = "Amawulire ga leero #Uganda #Bukedde"
    cleaned = clean_text(raw)
    assert "#Uganda" in cleaned
    assert "#Bukedde" in cleaned


def test_mentions_preserved_by_default():
    raw = "Kyogeddwako @Bukedde_ug mu lupapula"
    cleaned = clean_text(raw)
    assert "@Bukedde_ug" in cleaned


def test_hashtags_and_mentions_extracted_for_inspection():
    raw = "Wano @Bukedde_ug bawandiise #EbyaKawuka leero"
    found = extract_hashtags_and_mentions(raw)
    assert "@Bukedde_ug" in found["mentions"]
    assert "#EbyaKawuka" in found["hashtags"]


# --- combined social-text smoke test -------------------------------------------

def test_handle_social_edge_cases_combined():
    raw = "Yatuuka ku 9am ng'akozesa 4G 😂 @Bukedde_ug #breaking 50,000/="
    cleaned = handle_social_edge_cases(raw)
    assert "9am" in cleaned
    assert "4G" in cleaned
    assert "😂" not in cleaned
    assert "@Bukedde_ug" in cleaned
    assert "#breaking" in cleaned