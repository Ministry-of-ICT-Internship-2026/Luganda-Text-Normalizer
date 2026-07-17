"""
normalizer (distributed as "luganda-normalizer")
==================================================
A Python library for preprocessing Luganda text for NLP pipelines:
cleaning, elision expansion, abbreviation/acronym expansion, currency
and date/time expansion, number-to-words expansion, tokenization,
spelling standardization, noun/verb morphology stripping, and
English/Luganda code-switching detection.

Install (editable, from the project root -- see pyproject.toml):
    pip install -e .

Import:
    import normalizer
    normalizer.normalize("Abaana b'omu kibuga bazannya n'essanyu.")

or import individual pieces:
    from normalizer import tokenize, clean_text, normalize

Full pipeline
-------------
normalize(text)
    Runs clean_text -> normalize_diacritics -> expand_elisions ->
    expand_abbreviations -> expand_currency_to_words -> expand_datetimes
    -> expand_numbers -> tokenize -> lowercase -> standardize_tokens ->
    noun/verb stripping, and returns a single normalized string. This
    is the one-call entry point most callers want. Each of the four
    expansion stages can be toggled off with a keyword argument (see
    normalizer.pipeline.normalize's docstring / docs/architecture.md).

Building blocks (each stage is also exported on its own, so callers can
assemble a custom pipeline or unit-test a single step)
-------------------------------------------------------
Cleaning (normalizer.cleaner):
    clean_text, normalize_unicode, strip_control_characters,
    standardize_quotes_and_dashes, fix_spacing_before_punctuation,
    collapse_repeated_punctuation, collapse_whitespace

Elisions (normalizer.contractions):
    expand_elisions

Diacritics (normalizer.diacritics):
    normalize_diacritics, list_pending_reviews, add_confirmed_variant

Social-text / numeric edge cases (normalizer.edge_cases):
    fix_number_word_spacing, find_numeric_entities, extract_emoji,
    extract_hashtags_and_mentions, handle_social_edge_cases

Abbreviation / acronym expansion (normalizer.abbreviations):
    load_abbreviations, expand_abbreviations

Currency normalization (normalizer.currency):
    find_currency_entities, normalize_currency_format,
    amount_to_words, expand_currency_to_words

Date / time expansion (normalizer.datetime_expand):
    weekday_name, month_name, date_to_words, time_to_words,
    expand_dates, expand_times, expand_datetimes

Number-to-words expansion (normalizer.number_words):
    number_to_words, expand_numbers, NumberTooLargeError

Tokenization (normalizer.tokenizer):
    tokenize, diagnose

Spelling standardization (normalizer.spelling):
    load_dictionary, standardize_spelling, standardize_tokens

Morphology (normalizer.morphology_nouns / normalizer.morphology_verbs):
    NounStripper, VerbStripper

Code-switching detection (normalizer.code_switching):
    tag_token, tag_tokens, has_code_switching, annotate_code_switching

Stopwords / closed-class words (normalizer.stopwords):
    CLOSED_CLASS

Note on the package/import name
--------------------------------
The distribution installed via pip is named "luganda-normalizer" (see
pyproject.toml), but the importable package keeps the name "normalizer"
-- this matches how every module and test in this repo already imports
its siblings (e.g. `from normalizer.stopwords import CLOSED_CLASS`), and
mirrors common practice (e.g. the "beautifulsoup4" package is imported
as `bs4`). Always `import normalizer`, never `import luganda_normalizer`.

Several internal modules (pipeline.py, morphology_nouns.py,
morphology_verbs.py) deliberately use absolute imports like
`from normalizer.stopwords import CLOSED_CLASS` rather than relative
`.stopwords` imports. This is required for them to keep working once
pip-installed as the "normalizer" package -- do not "simplify" these to
relative imports without re-running the full test suite first, since
tests/test_morphology_nouns.py imports morphology_nouns.py as a
standalone top-level module and depends on this exact behaviour.
"""

# --- Full pipeline ----------------------------------------------------------
from normalizer.pipeline import normalize

# --- Cleaning -----------------------------------------------------------
from normalizer.cleaner import (
    clean_text,
    normalize_unicode,
    strip_control_characters,
    standardize_quotes_and_dashes,
    fix_spacing_before_punctuation,
    collapse_repeated_punctuation,
    collapse_whitespace,
)

# --- Elisions -------------------------------------------------------------
from normalizer.contractions import expand_elisions

# --- Diacritics -----------------------------------------------------------
from normalizer.diacritics import (
    normalize_diacritics,
    list_pending_reviews,
    add_confirmed_variant,
)

# --- Social-text / numeric edge cases --------------------------------------
from normalizer.edge_cases import (
    fix_number_word_spacing,
    find_numeric_entities,
    extract_emoji,
    extract_hashtags_and_mentions,
    handle_social_edge_cases,
)

# --- Abbreviation / acronym expansion ---------------------------------------
from normalizer.abbreviations import load_abbreviations, expand_abbreviations

# --- Currency normalization ---------------------------------------------------
from normalizer.currency import (
    find_currency_entities,
    normalize_currency_format,
    amount_to_words,
    expand_currency_to_words,
)

# --- Date / time expansion ----------------------------------------------------
from normalizer.datetime_expand import (
    weekday_name,
    month_name,
    date_to_words,
    time_to_words,
    expand_dates,
    expand_times,
    expand_datetimes,
)

# --- Number-to-words expansion -------------------------------------------------
from normalizer.number_words import number_to_words, expand_numbers, NumberTooLargeError

# --- Tokenization -----------------------------------------------------------
from normalizer.tokenizer import tokenize, diagnose

# --- Spelling standardization -----------------------------------------------
from normalizer.spelling import load_dictionary, standardize_spelling, standardize_tokens

# --- Morphology -------------------------------------------------------------
from normalizer.morphology_nouns import NounStripper
from normalizer.morphology_verbs import VerbStripper

# --- Code-switching detection -------------------------------------------------
from normalizer.code_switching import (
    tag_token,
    tag_tokens,
    has_code_switching,
    annotate_code_switching,
)

# --- Stopwords / closed-class words -----------------------------------------
from normalizer.stopwords import CLOSED_CLASS

__all__ = [
    # pipeline
    "normalize",
    # cleaner
    "clean_text",
    "normalize_unicode",
    "strip_control_characters",
    "standardize_quotes_and_dashes",
    "fix_spacing_before_punctuation",
    "collapse_repeated_punctuation",
    "collapse_whitespace",
    # contractions
    "expand_elisions",
    # diacritics
    "normalize_diacritics",
    "list_pending_reviews",
    "add_confirmed_variant",
    # edge cases
    "fix_number_word_spacing",
    "find_numeric_entities",
    "extract_emoji",
    "extract_hashtags_and_mentions",
    "handle_social_edge_cases",
    # abbreviations
    "load_abbreviations",
    "expand_abbreviations",
    # currency
    "find_currency_entities",
    "normalize_currency_format",
    "amount_to_words",
    "expand_currency_to_words",
    # datetime_expand
    "weekday_name",
    "month_name",
    "date_to_words",
    "time_to_words",
    "expand_dates",
    "expand_times",
    "expand_datetimes",
    # numbers
    "number_to_words",
    "expand_numbers",
    "NumberTooLargeError",
    # tokenizer
    "tokenize",
    "diagnose",
    # spelling
    "load_dictionary",
    "standardize_spelling",
    "standardize_tokens",
    # morphology
    "NounStripper",
    "VerbStripper",
    # code_switching
    "tag_token",
    "tag_tokens",
    "has_code_switching",
    "annotate_code_switching",
    # stopwords
    "CLOSED_CLASS",
]

__version__ = "0.1.0"
