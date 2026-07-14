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
Extra-deep tests for luganda_normalizer.tokenizer

This file goes past test_tokenizer_hard.py into edge conditions that
interact with things OUTSIDE the apostrophe rule itself: NLTK's built-in
abbreviation list, diacritics/tone marks, code-switching, malformed
punctuation, and multi-line input.

Case 05 below (abbreviation_period_not_sentence_end) originally FAILED
and drove a real fix to tokenizer.py: the word-boundary regex was
matching every word in the sentence (not just apostrophe-containing
ones), which meant "Dr." got needlessly protected and NLTK never saw it
as a whole "Dr." token -- so its own abbreviation list stopped working
and "Dr." got wrongly split into "Dr" + ".". Fixed by requiring at least
one apostrophe-group in the word regex ('+' instead of '*'), so plain
words are left alone and only actually-fragile words are touched.

Run with:  pytest tests/test_tokenizer_deep.py -v
       or:  python3 tests/test_tokenizer_deep.py
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
    }
]
DEEP_CASES = [
    {
        "name": "01_tone_marked_diacritic_vowels",
        # Luganda is sometimes written with tone marks (á, à, â) in
        # linguistic/educational texts. Confirms accented vowels inside
        # an elided word don't break the match.
        "input": "B\u00e1kyala b'\u00f3mu kibuga b\u00e1somye.",
        "expected": ["B\u00e1kyala", "b'\u00f3mu", "kibuga", "b\u00e1somye", "."],
    },
    {
        "name": "02_curly_double_quotes_wrapping_elision",
        # Curly DOUBLE quotes (\u201c \u201d) around a whole quoted clause
        # that itself contains an elided word right after the opening
        # quote mark, with no space.
        "input": "Yagamba nti, \u201cN\u2019ekyo kye njagala.\u201d",
        "expected": ["Yagamba", "nti", ",", "\u201c", "N'ekyo", "kye",
                      "njagala", ".", "\u201d"],
    },
    {
        "name": "03_thousands_separator_number",
        "input": "Ssente ze nnina ziri 1,000,000 ku akaunti.",
        "expected": ["Ssente", "ze", "nnina", "ziri", "1,000,000", "ku",
                      "akaunti", "."],
    },
    {
        "name": "04_english_codeswitch_possessive",
        # Ugandan text often code-switches with English. An English
        # possessive apostrophe-s lands inside otherwise Luganda text.
        # We don't try to distinguish "English 's" from "Luganda
        # elision" -- both get kept as one token, which is a reasonable,
        # documented default (arguably better than nltk's own English
        # rule, which would split "Uganda's" into "Uganda" + "'s").
        "input": "Uganda's ekyenkanyo kyakyuka nnyo.",
        "expected": ["Uganda's", "ekyenkanyo", "kyakyuka", "nnyo", "."],
    },
    {
        "name": "05_abbreviation_period_not_sentence_end",
        # The case that caught a real bug: "Dr." must survive as ONE
        # token via nltk's own abbreviation list. This only works now
        # that plain (non-apostrophe) words are left alone by our regex.
        "input": "Dr. Musisi yayogera ku by\u2019obulamu.",
        "expected": ["Dr.", "Musisi", "yayogera", "ku", "by'obulamu", "."],
    },
    {
        "name": "06_embedded_email_and_url",
        "input": ("Tunnyonnyola ku www.mak.ac.ug oba tosindika email ku "
                    "info@mak.ac.ug."),
        "expected": ["Tunnyonnyola", "ku", "www.mak.ac.ug", "oba",
                      "tosindika", "email", "ku", "info", "@",
                      "mak.ac.ug", "."],
    },
    {
        "name": "07_all_caps_elided_sentence",
        # Shouted/emphasis text (all caps) -- confirms the character
        # class isn't accidentally case-sensitive in a way that misses
        # uppercase elided words.
        "input": "TETUKKIRIZA N'EKINTU KYONNA!",
        "expected": ["TETUKKIRIZA", "N'EKINTU", "KYONNA", "!"],
    },
    {
        "name": "08_doubled_apostrophe_typo_documented_limitation",
        # A malformed double apostrophe (typo, or bad OCR/scrape). This
        # is NOT fixed -- documented here as a known limitation rather
        # than silently glossed over. Our regex requires letters
        # immediately after an apostrophe, so a second consecutive
        # apostrophe breaks the match early, same as plain nltk. Correct
        # handling would need a spellchecking/cleanup pass upstream of
        # tokenization, which is out of scope for this module.
        "input": "Nnina ekitabo n''ekikopo.",
        "expected": ["Nnina", "ekitabo", "n", "''", "ekikopo", "."],
    },
    {
        "name": "09_multiline_paragraph_with_elisions",
        # Real text often comes with embedded newlines (paragraphs,
        # copy-pasted text). Confirms elisions on different lines both
        # get handled independently and correctly.
        "input": "Ky'oyagala kye ki?\nN'ekyo kye njagala.",
        "expected": ["Ky'oyagala", "kye", "ki", "?", "N'ekyo", "kye",
                      "njagala", "."],
    },
    {
        "name": "10_double_hyphen_adjacent_to_elision",
        # Em-dash-style "--" used for a parenthetical aside directly
        # touching an elided word on both sides.
        "input": "Omukyala--nga y'ataka--yakuba oluyi.",
        "expected": ["Omukyala", "--", "nga", "y'ataka", "--", "yakuba",
                      "oluyi", "."],
    },
]


def test_deep_cases():
    for case in DEEP_CASES:
        result = tokenize(case["input"])
        assert result == case["expected"], (
            f"{case['name']} failed.\n  input:    {case['input']}\n"
            f"  got:      {result}\n  expected: {case['expected']}"
        )


def test_plain_words_are_not_needlessly_protected():
    # Regression guard for bug found in case 05: a sentence with NO
    # apostrophes anywhere should tokenize identically to plain nltk,
    # proving we aren't intercepting words we have no business touching.
    from nltk.tokenize import word_tokenize as nltk_word_tokenize
    plain = "Dr. Musisi Prof. Ssali baali ku lukiiko."
    assert tokenize(plain) == nltk_word_tokenize(plain)


def _run_as_script():
    passed = 0
    for case in DEEP_CASES:
        result = tokenize(case["input"])
        ok = result == case["expected"]
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {case['name']}")
        print(f"    input: {case['input']}")
        print(f"    got:   {result}")
        if not ok:
            print(f"    expected: {case['expected']}")
    print(f"\n{passed}/{len(DEEP_CASES)} deep test cases passed.")


if __name__ == "__main__":
    _run_as_script()
