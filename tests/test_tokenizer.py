"""
Extreme-edge tests for luganda_normalizer.tokenizer

This file goes past test_tokenizer_deep.py into conditions that stress
the interaction between our masking approach, NLTK's sentence/word
tokenization, and real-world text mess: chained elisions, abbreviations
colliding with elisions, missing whitespace, case sensitivity, emoji,
hyphenated compounds, and unusual apostrophe variants.

Every expected value below was verified against the actual tokenizer
output before being written into this file (not hand-guessed). Some
cases are marked DOCUMENTED LIMITATION: the expected value matches
current (imperfect) behavior on purpose, the same way case 08 in
test_tokenizer_deep.py documents the doubled-apostrophe gap instead of
silently ignoring it.

Cases 16-17 were originally KNOWN BUGs: a placeholder-namespace
collision in the masking mechanism itself (independent of Luganda
linguistics) could crash tokenize() with KeyError, or silently
substitute the wrong word into the output with no error at all, if the
raw input text happened to contain something shaped like the internal
placeholder tag. This was fixed in tokenizer.py (see Rule 8: a
collision-proof, per-call random placeholder tag). Both cases now
assert the FIXED, correct behavior and serve as regression tests for
this bug class going forward.

Run with:  pytest tests/test_tokenizer_extreme.py -v
       or:  python3 tests/test_tokenizer_extreme.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from normalizer.tokenizer import tokenize


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
        # a chance to split them -- they merge into a single token
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
        # NLTK's default behavior and gets its period split off.
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
        # \u2019 (U+2019). It survives here, but NOT because our regex
        # protects it -- it isn't in the apostrophe character class at
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
        # Real copy-pasted text often carries tabs and blank lines
        # between sentences/fields. Confirms two elisions separated by
        # whitespace noise (not just a single space) both survive
        # independently and correctly.
        "input": "Ky'oyagala\tkye ki?\n\nN'ekyo kye njagala.",
        "expected": ["Ky'oyagala", "kye", "ki", "?", "N'ekyo", "kye",
                      "njagala", "."],
    },
    {
        "name": "13_curly_apostrophe_adjacent_to_digit",
        # KNOWN BUG: the protection regex's letter class is
        # [A-Za-zŋŊ] only -- no digits. A straight apostrophe next to a
        # digit survives by NLTK coincidence, but the CURLY apostrophe
        # (the exact character the module's own docstring calls "the
        # confirmed breakage" for elision words) gets none of the
        # protection this module exists to provide, because the digit
        # falls outside the letter class the elision-word regex checks.
        "input": "N\u20192024 yali mwaka mulungi.",
        "expected": ["N", "\u2019", "2024", "yali", "mwaka", "mulungi", "."],
    },
    {
        "name": "14_doubled_apostrophe_typo",
        # KNOWN BUG (same class as test_tokenizer_deep.py case 08, but
        # placed here because it's the direct root cause behind case 13
        # too): a doubled apostrophe never matches _LUGANDA_WORD_RE at
        # all -- the repeated group requires a letter immediately after
        # every apostrophe -- so the word is never masked and gets
        # shredded exactly like plain nltk would shred it.
        "input": "n''ekitabo",
        "expected": ["n", "''", "ekitabo"],
    },
    {
        "name": "15_zero_width_space_inside_elision",
        # KNOWN BUG: a zero-width space (U+200B) -- a real copy-paste
        # artifact from some mobile keyboards/autocorrect chains --
        # breaks the apostrophe+letter match, so the word is never
        # masked. It happens to survive as ONE token because NLTK
        # doesn't tokenize on U+200B, but the returned string is NOT
        # equal to the clean word: it silently carries an invisible
        # character that will fail every downstream dictionary lookup
        # (spelling standardization, prefix/suffix stripping) with no
        # visible sign why.
        "input": "n'\u200bekitabo",
        "expected": ["n'\u200bekitabo"],
    },
    {
        "name": "16_literal_placeholder_tag_in_input",
        # FIXED (was a crash bug): raw input text that happens to
        # contain something shaped like the internal placeholder used to
        # be indistinguishable from a real placeholder generated by this
        # call, and crashed tokenize() with KeyError. Since the fix
        # (per-call random session tag, verified absent from the source
        # text before use -- see Rule 8 in tokenizer.py), literal text
        # shaped like "XLGWRDX0" now survives untouched, because the
        # actual placeholder tag used internally for this call is never
        # the fixed "XLGWRDX" string.
        "input": "Product code XLGWRDX0 was recalled.",
        "expected": ["Product", "code", "XLGWRDX0", "was", "recalled", "."],
    },
    {
        "name": "17_placeholder_index_collision_no_longer_substitutes",
        # FIXED (was a silent-corruption bug): literal text "XLGWRDX0"
        # in a sentence that ALSO contains a real elision used to get
        # silently swapped for an unrelated Luganda word whenever the
        # index happened to coincide with a real placeholder. Now the
        # literal text is preserved exactly as typed, and the real
        # elision is still protected correctly alongside it.
        "input": "n'ekitabo XLGWRDX0 b'omu",
        "expected": ["n'ekitabo", "XLGWRDX0", "b'omu"],
    },
]


def test_extreme_cases():
    for case in EXTREME_CASES:
        result = tokenize(case["input"])
        assert result == case["expected"], (
            f"{case['name']} failed.\n  input:    {case['input']!r}\n"
            f"  got:      {result}\n  expected: {case['expected']}"
        )


def test_plain_words_are_not_needlessly_protected():
    # Regression guard: a sentence with NO apostrophes anywhere should
    # tokenize identically to plain nltk, proving the masking layer
    # isn't intercepting words it has no business touching.
    from nltk.tokenize import word_tokenize as nltk_word_tokenize
    plain = "Dr. Musisi Prof. Ssali baali ku lukiiko."
    assert tokenize(plain) == nltk_word_tokenize(plain)


def _run_as_script():
    passed = 0
    total = 0

    print("=== EXTREME_CASES ===")
    for case in EXTREME_CASES:
        total += 1
        try:
            result = tokenize(case["input"])
        except Exception as e:
            print(f"[FAIL] {case['name']} (raised {type(e).__name__}: {e})")
            continue
        ok = result == case["expected"]
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {case['name']}")
        print(f"    input: {case['input']!r}")
        print(f"    got:   {result}")
        if not ok:
            print(f"    expected: {case['expected']}")

    print(f"\n{passed}/{total} extreme test cases passed.")


if __name__ == "__main__":
    _run_as_script()