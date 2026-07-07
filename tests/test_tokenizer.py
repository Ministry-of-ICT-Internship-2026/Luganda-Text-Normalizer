"""
Extreme-edge tests for luganda_normalizer.tokenizer

This file goes past test_tokenizer_deep.py into conditions that stress
the interaction between our masking approach, NLTK's sentence/word
tokenization, and real-world text mess: chained elisions, abbreviations
colliding with elisions, missing whitespace, case sensitivity, emoji,
hyphenated compounds, and unusual apostrophe variants.

Every expected value below was verified against the actual tokenizer
output before being written into this file (not hand-guessed) — see
the probe script used to generate them. Some cases are marked as
DOCUMENTED LIMITATIONS: the expected value matches current (imperfect)
behavior on purpose, the same way case 08 in test_tokenizer_deep.py
documents the doubled-apostrophe gap instead of silently ignoring it.

Run with:  pytest tests/test_tokenizer_extreme.py -v
       or:  python3 tests/test_tokenizer_extreme.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tokenizer import tokenize


EXTREME_CASES = [
    {
        "name": "01_chained_double_elision",
        # Two elisions chained onto the same word root, no space between
        # them. Confirms the '+' (one-or-more apostrophe-groups) design
        # handles more than one elision boundary, not just one.
        "input": "Ky'omu'lukiiko yajja.",
        "expected": ["Ky'omu'lukiiko", "yajja", "."],
    },
    {
        "name": "02_abbreviation_at_sentence_end",
        # "Dr." is BOTH the abbreviation period AND the sentence-ending
        # period at once (only one period exists in the source text).
        # Confirms we don't invent a phantom second period.
        "input": "Yali mulwadde, Dr.",
        "expected": ["Yali", "mulwadde", ",", "Dr."],
    },
    {
        "name": "03_two_abbreviations_back_to_back",
        "input": "Dr. Mr. Musisi baazze.",
        "expected": ["Dr.", "Mr.", "Musisi", "baazze", "."],
    },
    {
        "name": "04_abbreviation_immediately_before_elision_no_space",
        # DOCUMENTED LIMITATION: no space between an abbreviation and
        # the next (elided) word. Both get masked as separate
        # placeholders, but since nothing separates them in the source
        # text, NLTK sees one unbroken alphanumeric blob and never gets
        # a chance to split them — they merge into a single token
        # instead of "Dr." + "Ng'enda". A real fix would need explicit
        # boundary detection between two adjacent protected spans,
        # which is out of scope here; flagged for the team to decide
        # whether malformed (no-space) input like this is worth
        # handling, or left as an upstream data-cleaning problem.
        "input": "Dr.Ng'enda yagenze.",
        "expected": ["Dr.Ng'enda", "yagenze", "."],
    },
    {
        "name": "05_unknown_abbreviation_not_in_list",
        # DOCUMENTED LIMITATION: our _ABBREVIATIONS set is a fixed,
        # hand-picked list (Dr, Mr, Mrs, Ms, Prof, St, Rev, Gen, Sgt).
        # Anything outside it (e.g. "Bp." for Bishop) falls back to
        # NLTK's default behavior and gets its period split off. This
        # is the same bug case 05 in test_tokenizer_deep.py fixed for
        # "Dr." specifically — it is NOT fixed in general. Whoever owns
        # corpus analysis should surface real Luganda-context
        # abbreviations to add to the list.
        "input": "Bp. Ssali yayogedde.",
        "expected": ["Bp", ".", "Ssali", "yayogedde", "."],
    },
    {
        "name": "06_left_and_right_curly_quotes_wrapping_elision",
        "input": "Yagamba nti \u2018Ky'omu si kirungi.\u2019",
        "expected": ["Yagamba", "nti", "\u2018", "Ky'omu", "si",
                      "kirungi", ".", "\u2019"],
    },
    {
        "name": "07_modifier_letter_apostrophe_variant",
        # \u02bc (MODIFIER LETTER APOSTROPHE) is the "correct" Unicode
        # character for glottal/elision marks in several African-
        # language orthographies, distinct from both ' (U+0027) and
        # ’ (U+2019). It survives here, but NOT because our regex
        # protects it — it isn't in the apostrophe character class at
        # all. It survives by the same "NLTK coincidence" the module
        # docstring already warns about for the straight quote. Worth
        # deciding as a team whether \u02bc should be added to the
        # protected character class explicitly rather than relying on
        # coincidence.
        "input": "Ky\u02bcomu ky'ekitiibwa.",
        "expected": ["Ky\u02bcomu", "ky'ekitiibwa", "."],
    },
    {
        "name": "08_hyphenated_compound_with_elision",
        # Hyphenated compound where one half contains an elision.
        # NLTK's own hyphen handling (keeps hyphenated compounds as one
        # token) combines with our masking to keep the whole thing
        # together, hyphen included.
        "input": "Ky'omu-nnyumba yaakyuka.",
        "expected": ["Ky'omu-nnyumba", "yaakyuka", "."],
    },
    {
        "name": "09_multiple_sentences_shared_abbreviation",
        "input": "Dr. Musisi yajja. Dr. Ssali naye yajja.",
        "expected": ["Dr.", "Musisi", "yajja", ".", "Dr.", "Ssali",
                      "naye", "yajja", "."],
    },
    {
        "name": "10_elision_immediately_before_a_number",
        "input": "N'ekitundu 5 kyali kirungi.",
        "expected": ["N'ekitundu", "5", "kyali", "kirungi", "."],
    },
    {
        "name": "11_emoji_adjacent_to_elision",
        "input": "Ky'omu \U0001F600 kirungi nnyo.",
        "expected": ["Ky'omu", "\U0001F600", "kirungi", "nnyo", "."],
    },
    {
        "name": "12_tabs_and_blank_lines_between_elisions",
        "input": "Ky'oyagala\tkye ki?\n\nN'ekyo kye njagala.",
        "expected": ["Ky'oyagala", "kye", "ki", "?", "N'ekyo", "kye",
                      "njagala", "."],
    },
    {
        "name": "13_elision_inside_parentheses",
        "input": "(N'ekyo kye njagala) nabadde ntyo.",
        "expected": ["(", "N'ekyo", "kye", "njagala", ")", "nabadde",
                      "ntyo", "."],
    },
    {
        "name": "14_triple_elision_in_one_sentence",
        "input": "Ky'omu n'ekyo ky'ekitiibwa byonna bya muzeeyi.",
        "expected": ["Ky'omu", "n'ekyo", "ky'ekitiibwa", "byonna",
                      "bya", "muzeeyi", "."],
    },
    {
        "name": "15_lowercase_abbreviation_case_sensitivity",
        # DOCUMENTED LIMITATION: the abbreviation match is case-
        # sensitive (only "Dr", not "dr"). Real scraped/social text is
        # often all-lowercase. Fix would mean matching case-
        # insensitively but PRESERVING original casing on output —
        # not yet implemented.
        "input": "dr. musisi yali wano.",
        "expected": ["dr", ".", "musisi", "yali", "wano", "."],
    },
    {
        "name": "16_colon_immediately_before_elision",
        "input": "Yategeezezza bwati: n'ekyo kye kirungi.",
        "expected": ["Yategeezezza", "bwati", ":", "n'ekyo", "kye",
                      "kirungi", "."],
    },
]


def test_extreme_cases():
    for case in EXTREME_CASES:
        result = tokenize(case["input"])
        assert result == case["expected"], (
            f"{case['name']} failed.\n  input:    {case['input']}\n"
            f"  got:      {result}\n  expected: {case['expected']}"
        )


def test_case_sensitive_abbreviation_is_a_known_gap():
    # Explicit regression guard, separate from the main loop, so this
    # limitation can't silently start passing/failing without someone
    # noticing and updating the module docstring accordingly.
    result = tokenize("dr. musisi yali wano.")
    assert result[0] == "dr" and result[1] == "."


def test_unlisted_abbreviation_is_a_known_gap():
    result = tokenize("Bp. Ssali yayogedde.")
    assert result[0] == "Bp" and result[1] == "."


def _run_as_script():
    passed = 0
    for case in EXTREME_CASES:
        result = tokenize(case["input"])
        ok = result == case["expected"]
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {case['name']}")
        print(f"    input: {case['input']}")
        print(f"    got:   {result}")
        if not ok:
            print(f"    expected: {case['expected']}")
    print(f"\n{passed}/{len(EXTREME_CASES)} extreme test cases passed.")


if __name__ == "__main__":
    _run_as_script()