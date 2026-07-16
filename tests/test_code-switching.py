# test_code_switching.py
"""Tests for normalizer/code_switching.py."""

from normalizer.codeswitching import (
    tag_token,
    tag_tokens,
    has_code_switching,
    annotate_code_switching,
)


class TestTagToken:
    def test_known_luganda_noun(self):
        result = tag_token("omusajja")
        assert result["tag"] == "LUG"
        assert result["method"] == "lexicon"

    def test_known_luganda_verb_root(self):
        result = tag_token("okugenda")
        assert result["tag"] == "LUG"

    def test_closed_class_word(self):
        result = tag_token("kubanga")
        assert result["tag"] == "LUG"

    def test_common_english_word(self):
        result = tag_token("stress")
        assert result["tag"] == "ENG"
        assert result["method"] == "lexicon"

    def test_number_tagged_as_num(self):
        result = tag_token("123")
        assert result["tag"] == "NUM"

    def test_negative_number_tagged_as_num(self):
        result = tag_token("-5")
        assert result["tag"] == "NUM"

    def test_punctuation_only_tagged_as_punct(self):
        result = tag_token("!!!")
        assert result["tag"] == "PUNCT"

    def test_unknown_word_tagged_as_unk_not_guessed(self):
        result = tag_token("xyzzyplugh")
        assert result["tag"] == "UNK"
        assert result["method"] == "none"

    def test_case_insensitive_lookup(self):
        assert tag_token("STRESS")["tag"] == "ENG"
        assert tag_token("Omusajja")["tag"] == "LUG"

    def test_trailing_punctuation_stripped_before_lookup(self):
        result = tag_token("stress,")
        assert result["tag"] == "ENG"


class TestTagTokens:
    def test_tags_a_mixed_sentence(self):
        tokens = ["omusajja", "abadde", "ne", "stress", "nnyo"]
        results = tag_tokens(tokens)
        assert len(results) == 5
        assert results[0]["tag"] == "LUG"
        assert results[3]["tag"] == "ENG"

    def test_empty_list(self):
        assert tag_tokens([]) == []


class TestHasCodeSwitching:
    def test_detects_real_code_switching(self):
        tokens = ["omusajja", "abadde", "ne", "stress", "nnyo"]
        assert has_code_switching(tokens) is True

    def test_all_luganda_is_not_code_switching(self):
        tokens = ["omusajja", "kibuga", "kubanga"]
        assert has_code_switching(tokens) is False

    def test_all_english_is_not_code_switching(self):
        # No Luganda lexicon hit present, so this isn't "switching"
        # between two languages by this function's definition.
        tokens = ["the", "meeting", "is", "today"]
        assert has_code_switching(tokens) is False

    def test_empty_list_is_not_code_switching(self):
        assert has_code_switching([]) is False

    def test_unknown_words_alone_do_not_count(self):
        tokens = ["xyzzyplugh", "qwertyuiop"]
        assert has_code_switching(tokens) is False


class TestAnnotateCodeSwitching:
    def test_wraps_english_word_only(self):
        result = annotate_code_switching("omusajja abadde ne stress nnyo.")
        assert "[ENG]stress[/ENG]" in result
        assert "omusajja" in result and "[ENG]omusajja[/ENG]" not in result

    def test_preserves_trailing_punctuation_outside_markers(self):
        result = annotate_code_switching("Yali stress, nnyo.")
        assert "[ENG]stress[/ENG]," in result

    def test_no_english_words_returns_unchanged(self):
        text = "omusajja kibuga kubanga"
        assert annotate_code_switching(text) == text

    def test_never_deletes_or_reorders_words(self):
        text = "omusajja abadde ne stress z'awaka."
        result = annotate_code_switching(text)
        # Every original word should still appear somewhere in the result.
        for word in text.split(" "):
            core = word.strip(".,!?;:\"'()")
            assert core in result