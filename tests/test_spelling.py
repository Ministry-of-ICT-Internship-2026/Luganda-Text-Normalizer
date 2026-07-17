"""
Tests for standardize_spelling.py

Run with:  pytest -v
(pytest must be able to import the module — this file adds the parent
directory to sys.path, so it works whether run from repo root or from
inside tests/.)
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from normalizer import spelling as ss


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mappings():
    """A small, self-contained mapping table so tests don't depend on the
    real dictionary file (whose contents may change over time)."""
    return {
        "sebo": "ssebo",
        "webale": "webaale",
        "Kampala": "Kampala",  # already canonical, mixed case in dict
    }


# ---------------------------------------------------------------------------
# standardize_spelling: core replacement behavior
# ---------------------------------------------------------------------------

class TestBasicReplacement:
    def test_known_word_is_replaced(self, mappings):
        assert ss.standardize_spelling("sebo", mappings) == "ssebo"

    def test_unknown_word_passes_through_unchanged(self, mappings):
        assert ss.standardize_spelling("unmapped_word_xyz", mappings) == "unmapped_word_xyz"

    def test_sentence_with_mixed_known_and_unknown_words(self, mappings):
        result = ss.standardize_spelling("sebo how are you webale", mappings)
        assert result == "ssebo how are you webaale"

    def test_multiple_known_words_in_one_sentence(self, mappings):
        result = ss.standardize_spelling("sebo sebo webale", mappings)
        assert result == "ssebo ssebo webaale"


class TestCaseHandling:
    def test_case_insensitive_by_default(self, mappings):
        assert ss.standardize_spelling("SEBO", mappings) == "ssebo"
        assert ss.standardize_spelling("Sebo", mappings) == "ssebo"

    def test_replacement_uses_dictionary_canonical_casing_not_input_casing(self, mappings):
        # Regardless of how the input word was capitalized, the output
        # should be the dictionary's canonical form.
        assert ss.standardize_spelling("SeBo", mappings) == "ssebo"

    def test_case_sensitive_mode_requires_exact_match(self, mappings):
        # "SEBO" has no exact-case entry in `mappings`, so it should be
        # left untouched when case_sensitive=True.
        assert ss.standardize_spelling("SEBO", mappings, case_sensitive=True) == "SEBO"

    def test_case_sensitive_mode_matches_exact_case(self, mappings):
        assert ss.standardize_spelling("sebo", mappings, case_sensitive=True) == "ssebo"


class TestPunctuationHandling:
    def test_trailing_period_is_preserved(self, mappings):
        assert ss.standardize_spelling("webale.", mappings) == "webaale."

    def test_trailing_punctuation_bundle_is_preserved(self, mappings):
        assert ss.standardize_spelling("sebo?!", mappings) == "ssebo?!"

    def test_KNOWN_BUG_leading_punctuation_corrupts_output(self, mappings):
        # BUG: `trailing = word[len(stripped):]` assumes strip() only
        # removed characters from the END of `word`. When there's also
        # LEADING punctuation, `stripped` is shorter than it "should" be
        # relative to the tail, so the slice grabs part of the matched
        # word itself and duplicates it onto the output.
        # '"sebo"' -> stripped="sebo" (len 4) -> trailing=word[4:]='o"'
        # -> result = "ssebo" + 'o"' = 'sseboo"'  (clearly wrong)
        result = ss.standardize_spelling('"sebo"', mappings)
        assert result == 'sseboo"'  # documents current (buggy) behavior
        assert result != "ssebo"  # what a user would actually expect

    def test_word_of_only_punctuation_is_untouched(self, mappings):
        assert ss.standardize_spelling("...", mappings) == "..."

    def test_unknown_word_with_punctuation_passes_through_unchanged(self, mappings):
        assert ss.standardize_spelling("xyz.", mappings) == "xyz."


class TestWhitespaceAndEmptyInput:
    def test_empty_string_returns_empty_string(self, mappings):
        assert ss.standardize_spelling("", mappings) == ""

    def test_none_input_does_not_raise(self, mappings):
        # `if not text: return text` should short-circuit before any
        # attribute access on None.
        assert ss.standardize_spelling(None, mappings) is None

    def test_double_spaces_are_preserved(self, mappings):
        result = ss.standardize_spelling("sebo  webale", mappings)
        assert result == "ssebo  webaale"

    def test_single_word_no_spaces(self, mappings):
        assert ss.standardize_spelling("webale", mappings) == "webaale"


class TestMappingsParameterDefaultsToFile:
    def test_none_mappings_loads_default_dictionary(self):
        # Uses the real spelling_dictionary.json shipped alongside the module.
        result = ss.standardize_spelling("sebo")
        assert result == "ssebo"

    def test_default_dictionary_handles_unknown_word(self):
        result = ss.standardize_spelling("totally_not_a_real_word")
        assert result == "totally_not_a_real_word"


# ---------------------------------------------------------------------------
# standardize_tokens
# ---------------------------------------------------------------------------

class TestStandardizeTokens:
    def test_replaces_known_tokens(self, mappings):
        tokens = ["sebo", "webale", "unknown"]
        assert ss.standardize_tokens(tokens, mappings) == ["ssebo", "webaale", "unknown"]

    def test_case_insensitive_lookup(self, mappings):
        assert ss.standardize_tokens(["SEBO"], mappings) == ["ssebo"]

    def test_empty_token_list(self, mappings):
        assert ss.standardize_tokens([], mappings) == []

    def test_none_mappings_loads_default_dictionary(self):
        assert ss.standardize_tokens(["sebo"]) == ["ssebo"]

    def test_does_not_strip_punctuation_unlike_standardize_spelling(self, mappings):
        # standardize_tokens has no punctuation-stripping logic, so a
        # token with trailing punctuation will NOT match the dictionary.
        assert ss.standardize_tokens(["sebo."], mappings) == ["sebo."]


# ---------------------------------------------------------------------------
# load_dictionary
# ---------------------------------------------------------------------------

class TestLoadDictionary:
    def test_loads_real_dictionary_file(self):
        loaded = ss.load_dictionary()
        assert isinstance(loaded, dict)
        assert loaded.get("sebo") == "ssebo"
        assert len(loaded) > 0

    def test_missing_file_returns_empty_dict(self, tmp_path):
        missing_path = tmp_path / "does_not_exist.json"
        assert ss.load_dictionary(str(missing_path)) == {}

    def test_corrupt_json_returns_empty_dict(self, tmp_path):
        bad_file = tmp_path / "corrupt.json"
        bad_file.write_text("{ this is not valid json ", encoding="utf-8")
        assert ss.load_dictionary(str(bad_file)) == {}

    def test_valid_json_missing_mappings_key_returns_empty_dict(self, tmp_path):
        no_mappings_file = tmp_path / "no_mappings.json"
        no_mappings_file.write_text(json.dumps({"_meta": {}}), encoding="utf-8")
        assert ss.load_dictionary(str(no_mappings_file)) == {}

    def test_valid_custom_dictionary_loads_correctly(self, tmp_path):
        custom_file = tmp_path / "custom.json"
        custom_file.write_text(
            json.dumps({"mappings": {"foo": "bar"}}), encoding="utf-8"
        )
        assert ss.load_dictionary(str(custom_file)) == {"foo": "bar"}

    def test_empty_json_object_returns_empty_dict(self, tmp_path):
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}", encoding="utf-8")
        assert ss.load_dictionary(str(empty_file)) == {}


# ---------------------------------------------------------------------------
# Sanity checks against the real shipped dictionary file
# ---------------------------------------------------------------------------

class TestRealDictionaryFile:
    """These guard against accidental corruption of spelling_dictionary.json
    itself (e.g. a bad edit breaking JSON syntax or the schema)."""

    def test_dictionary_file_is_valid_json_with_expected_shape(self):
        path = ss.DEFAULT_DICT_PATH
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "mappings" in data
        assert isinstance(data["mappings"], dict)
        assert len(data["mappings"]) > 0

    def test_all_mapping_values_are_non_empty_strings(self):
        mappings = ss.load_dictionary()
        for variant, canonical in mappings.items():
            assert isinstance(variant, str) and variant.strip()
            assert isinstance(canonical, str) and canonical.strip()

    def test_sentence_from_module_smoke_test_normalizes_as_expected(self):
        result = ss.standardize_spelling("Sebo, webale nnyo ku bulunji bwo.")
        # "Sebo," -> "ssebo," / "webale" -> "webaale" / "bulunji" -> "bulungi"
        assert result == "ssebo, webaale nnyo ku bulungi bwo."
