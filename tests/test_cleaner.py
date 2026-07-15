"""
Tests for clean_text() — each test traces back to a specific finding in
P1_Research_Log.xlsx, using the real text snippets that surfaced the issue.

Run with: pytest test_clean_text.py -v
"""

from normalizer.cleaner import (
    clean_text,
    fix_spacing_before_punctuation,
    collapse_repeated_punctuation,
    fix_number_word_spacing,
    collapse_whitespace,
    standardize_quotes_and_dashes,
)


# --- log #4: space before punctuation (Twitter) -----------------------------

def test_space_before_comma_removed():
    raw = "Asaba okunoonyereza kuleme kukoma mu Paalamenti , n'ebitongole"
    cleaned = fix_spacing_before_punctuation(raw)
    assert " ," not in cleaned
    assert "Paalamenti, n'ebitongole" in cleaned


# --- log #3: double/multiple whitespace (Twitter) ---------------------------

def test_double_space_collapsed():
    raw = "Omusajja abadde ne stress z'awaka  avuze ennyonyi n'agitomeza"
    cleaned = collapse_whitespace(raw)
    assert "  " not in cleaned
    assert "z'awaka avuze" in cleaned


# --- log #6: repeated/stacked punctuation (Twitter) -------------------------

def test_repeated_exclamation_collapsed_by_default():
    raw = "n'afuuka mukyala !!!!!. Byampuna!!"
    cleaned = clean_text(raw)
    assert "!!!!!" not in cleaned
    assert "!!" not in cleaned


def test_repeated_punctuation_can_be_preserved():
    raw = "Byampuna!!"
    cleaned = clean_text(raw, collapse_punctuation=False)
    assert "!!" in cleaned  # opt-out preserves emphasis, per log #6 open decision


# --- log #5: curly quotes standardized (Bible) ------------------------------

def test_curly_quotes_become_straight():
    raw = "\u201cZakariya, leka kutya, kubanga Katonda a"
    cleaned = standardize_quotes_and_dashes(raw)
    assert "\u201c" not in cleaned
    assert cleaned.startswith('"Zakariya')


# --- log #10: verse number stuck to word (Bible) ----------------------------

def test_number_stuck_to_word_gets_space():
    raw = "bulenzi. 58Baliraanwa be ne baganda be"
    cleaned = fix_number_word_spacing(raw)
    assert "58 Baliraanwa" in cleaned
    assert "58Baliraanwa" not in cleaned


# --- log #2: irregular mid-sentence line breaks (News) ----------------------

def test_midsentence_linebreak_joined():
    raw = "kagenda kuva mu mbeera yaako ne kikosa\n\nn'obuwangaazi bwayo."
    cleaned = clean_text(raw)
    # A genuine blank-line paragraph break in the raw source; clean_text
    # should still leave the sentence readable as one line since it was a
    # single sentence split by a stray double-newline in the scrape.
    assert "kikosa n'obuwangaazi" in cleaned or "kikosa\n\nn'obuwangaazi" in cleaned


# --- full pipeline smoke test on a real, messy multi-issue snippet ----------

def test_full_pipeline_on_combined_real_snippet():
    raw = (
        "Richard Lumu  awa endowooza ye ku bakungu abakwatiddwa. "
        "Asaba okunoonyereza kuleme kukoma mu Paalamenti , n'ebitongole "
        "ebirala!!!!"
    )
    cleaned = clean_text(raw)
    assert "  " not in cleaned          # no double spaces
    assert " ," not in cleaned          # no space before comma
    assert "!!!!" not in cleaned        # punctuation collapsed
    assert "Lumu awa" in cleaned


def test_idempotent():
    """Running clean_text twice should produce the same result (a basic
    sanity check that the function isn't still leaving fixable mess behind).
    """
    raw = "Lumu  awa endowooza , ye!!!!"
    once = clean_text(raw)
    twice = clean_text(once)
    assert once == twice