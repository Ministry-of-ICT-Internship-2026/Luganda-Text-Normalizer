# test_abbreviations.py
"""Tests for normalizer/abbreviations.py."""

import json

import pytest

from normalizer.abbreviations import (
    load_abbreviations,
    expand_abbreviations,
    DEFAULT_DICT_PATH,
)


@pytest.fixture
def tables():
    """A small, self-contained table so tests don't depend on the real
    dictionary file's exact contents."""
    return {
        "case_sensitive": {"URA": "Uganda Revenue Authority", "KCCA": "Kampala Capital City Authority"},
        "case_insensitive": {"Dr": "Dokita", "e.g.": "gamba nga", "etc": "n'ebirala"},
    }


class TestExpandAbbreviationsWithCustomTables:
    def test_organization_acronym_expanded(self, tables):
        assert expand_abbreviations("URA basoma tax.", tables) == "Uganda Revenue Authority basoma tax."

    def test_acronym_is_case_sensitive(self, tables):
        # lowercase "ura" is NOT the acronym -- must not be expanded.
        assert expand_abbreviations("ura si kimu.", tables) == "ura si kimu."

    def test_title_expanded_case_insensitively(self, tables):
        assert expand_abbreviations("dr Ssebunya", tables) == "Dokita Ssebunya"
        assert expand_abbreviations("DR Ssebunya", tables) == "Dokita Ssebunya"

    def test_punctuation_ending_abbreviation_expanded(self, tables):
        result = expand_abbreviations("ebintu, e.g. emmere.", tables)
        assert result == "ebintu, gamba nga emmere."

    def test_unmapped_word_passes_through(self, tables):
        text = "Ekintu ekitali kumanyibwa XYZ."
        assert expand_abbreviations(text, tables) == text

    def test_does_not_match_substring_inside_larger_word(self, tables):
        # "URA" should not match inside "URAKAMU" or similar.
        text = "URAKAMU akola emirimu."
        assert expand_abbreviations(text, tables) == text

    def test_multiple_abbreviations_in_one_sentence(self, tables):
        result = expand_abbreviations("URA ne KCCA babadde wamu.", tables)
        assert result == "Uganda Revenue Authority ne Kampala Capital City Authority babadde wamu."

    def test_empty_string(self, tables):
        assert expand_abbreviations("", tables) == ""


class TestLoadAbbreviations:
    def test_returns_expected_shape(self):
        loaded = load_abbreviations()
        assert "case_sensitive" in loaded
        assert "case_insensitive" in loaded

    def test_missing_file_returns_empty_tables(self, tmp_path):
        missing = tmp_path / "does_not_exist.json"
        loaded = load_abbreviations(str(missing))
        assert loaded == {"case_sensitive": {}, "case_insensitive": {}}

    def test_corrupt_json_returns_empty_tables(self, tmp_path):
        bad_file = tmp_path / "corrupt.json"
        bad_file.write_text("{ not valid json", encoding="utf-8")
        loaded = load_abbreviations(str(bad_file))
        assert loaded == {"case_sensitive": {}, "case_insensitive": {}}

    def test_custom_file_loads_correctly(self, tmp_path):
        custom = tmp_path / "custom.json"
        custom.write_text(
            json.dumps({
                "organizations": {"FOO": "Full Organization Name"},
                "titles": {"Bar": "Barword"},
                "cross_language": {},
            }),
            encoding="utf-8",
        )
        loaded = load_abbreviations(str(custom))
        assert loaded["case_sensitive"] == {"FOO": "Full Organization Name"}
        assert loaded["case_insensitive"] == {"Bar": "Barword"}


class TestRealDictionaryFile:
    """Guard against accidental corruption of abbreviations_dictionary.json."""

    def test_dictionary_file_is_valid_json(self):
        with open(DEFAULT_DICT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "organizations" in data
        assert "titles" in data
        assert "cross_language" in data

    def test_ura_is_present_and_correct(self):
        loaded = load_abbreviations()
        assert loaded["case_sensitive"].get("URA") == "Uganda Revenue Authority"

    def test_all_values_are_non_empty_strings(self):
        loaded = load_abbreviations()
        for table in (loaded["case_sensitive"], loaded["case_insensitive"]):
            for key, value in table.items():
                assert isinstance(key, str) and key.strip()
                assert isinstance(value, str) and value.strip()

    def test_real_sentence_smoke_test(self):
        result = expand_abbreviations("URA yasoma ripoota, e.g. eby'omusolo.")
        assert "Uganda Revenue Authority" in result
        assert "gamba nga" in result
