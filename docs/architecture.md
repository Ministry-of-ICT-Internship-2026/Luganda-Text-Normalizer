# Architecture

## Overview

The Luganda Text Normalizer is a modular NLP preprocessing library.
Each stage is implemented independently, in its own module, and can be
used on its own or combined through `pipeline.normalize()`. Every
module degrades safely: unknown or malformed input passes through
unchanged rather than raising, and optional data files (dictionaries,
lexicons) fail open to a no-op instead of crashing the pipeline.

## Processing Flow

`normalize()` runs the following stages in order. The ordering is
deliberate — see the inline comments in `pipeline.py` for the
reasoning behind each dependency.

```text
Raw Text
    │
    ▼
Cleaner                        (cleaner.py)
    │
    ▼
Diacritic Normalizer           (diacritics.py)
    │
    ▼
Elision Expander                (contractions.py)
    │
    ▼
Abbreviation / Acronym Expansion (abbreviations.py)   ── case-sensitive, so runs before lowercasing
    │
    ▼
Currency Expansion              (currency.py)          ── before number expansion, consumes amount digits
    │
    ▼
Date / Time Expansion           (datetime.py)           ── before number expansion, consumes date/time digits
    │
    ▼
Number Expansion                (numbers.py)             ── phone numbers protected via edge_cases.PHONE_NUMBER_RE
    │
    ▼
Tokenizer                       (tokenizer.py)
    │
    ▼
Lowercase
    │
    ▼
Spelling Standardizer           (spelling.py)
    │
    ▼
Noun Prefix Stripper            (morphology_nouns.py)
    │
    ▼
Verb Affix Stripper             (morphology_verbs.py)
    │
    ▼
Normalized Output
```

Code-switching detection (`codeswitching.py`) and social-text edge-case
handling (`edge_cases.py`) are not part of the default `normalize()`
sequence — they're utilities callers opt into separately, since they
produce annotations/metadata rather than a further-normalized string.

## Core Modules

| Module | Responsibility |
|---|---|
| `cleaner.py` | Unicode cleanup, punctuation normalization, whitespace handling |
| `diacritics.py` | Canonical spelling and diacritic (incl. apostrophe-variant) normalization |
| `contractions.py` | Luganda elision expansion (`n'` → `na`) |
| `abbreviations.py` | Acronym (`URA`), honorific (`Dr.`), and cross-language (`e.g.`) expansion |
| `currency.py` | Currency detection and verbalization (`UGX 20,000` → words) |
| `datetime.py` | Date and time expansion |
| `numbers.py` | Number-to-words conversion |
| `tokenizer.py` | Apostrophe-aware tokenization |
| `spelling.py` | Dictionary-based spelling normalization |
| `morphology_nouns.py` | Noun-class prefix stripping |
| `morphology_verbs.py` | Verb affix stripping |
| `codeswitching.py` | Lexicon-based English/Luganda code-switch tagging and annotation |
| `edge_cases.py` | Social-text handling: emoji, hashtags/mentions, phone-number protection |
| `stopwords.py` | `CLOSED_CLASS` particle list, shared by several modules |
| `pipeline.py` | End-to-end orchestration (`normalize()`) |

## Data Files

| File | Used by | Format |
|---|---|---|
| `normalizer/spelling_dictionary.json` | `spelling.py` | `{"mappings": {variant: canonical, ...}}` |
| `normalizer/abbreviations_dictionary.json` | `abbreviations.py` | `{"organizations": {...}, "titles": {...}, "cross_language": {...}}` |
| `normalizer/lexicon_data/nouns.txt`, `verbs.txt` | `codeswitching.py` | Packaged copies of `data/nouns.txt` / `data/verbs.txt`, kept in sync manually |
| `data/nouns.txt`, `data/verbs.txt` | `morphology_nouns.py`, `morphology_verbs.py`, tests | Tab-separated: surface form, class/root, description |

`spelling_dictionary.json` and `abbreviations_dictionary.json` ship
inside the `normalizer` package (declared under
`[tool.setuptools.package-data]` in `pyproject.toml`) so they're
available after a `pip install`, not just in a source checkout. All
three loaders (`spelling.load_dictionary`, `abbreviations.load_abbreviations`,
and `codeswitching`'s internal lexicon builder) return empty/no-op
tables rather than raising if a data file is missing or malformed.

## Design Principles

- **Modular** — every stage is independently testable and importable.
- **Deterministic** — same input always produces the same output.
- **Luganda-first** — apostrophes, elisions, and noun classes are
  treated as first-class citizens, not edge cases bolted onto an
  English-oriented tokenizer.
- **Fail open, never crash** — a missing or corrupt dictionary file
  degrades a stage to a no-op instead of breaking the whole pipeline.
- **Preserve rather than guess** — code-switched English and unknown
  tokens are left untouched, not silently rewritten.
- **Lightweight** — minimal runtime dependencies (`nltk` only).
- **Composable** — applications may run only the stages they need.

## Public API

```python
import normalizer

normalizer.normalize(text)
normalizer.tokenize(text)
normalizer.clean_text(text)
normalizer.expand_elisions(text)
normalizer.expand_abbreviations(text)
normalizer.expand_currency_to_words(text)
normalizer.expand_datetimes(text)
normalizer.expand_numbers(text)
normalizer.standardize_spelling(text)
normalizer.tag_tokens(tokens)
normalizer.has_code_switching(tokens)
```

The full exported surface (every public function/class per stage) is
documented in `normalizer/__init__.py`'s module docstring.

## Recommended Usage

- **Search indexing:** cleaning + tokenization + spelling
- **Embeddings / ML features:** full normalization pipeline
- **Spell checking:** `spelling.py` module only
- **Corpus preparation:** full pipeline with morphology stripping
- **Code-switch–aware corpora:** full pipeline, then `codeswitching.py`
  on the tokenized output for tagging/annotation