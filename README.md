# Luganda Text Normalizer

A modular Python library for preprocessing Luganda text for search,
embeddings, spell-checking, machine learning, and other NLP tasks.

It handles the things generic (English-first) NLP tooling gets wrong for
Luganda: apostrophe-based elisions (`n'`, `ky'`), noun-class prefixes,
verb affixes, and everyday English/Luganda code-switching.

## Installation

```bash
pip install -e .
```

This installs the importable package `normalizer` (the PyPI/distribution
name is `luganda-normalizer`, but you always `import normalizer`).

## Quick Start

```python
import normalizer as n

text = "Abaana b'omu kibuga bazannya n'essanyu."

# Full pipeline
print(n.normalize(text))

# Tokenization only
print(n.tokenize("n'ekitabo ky'omusomesa"))
```

## What the pipeline does

`normalize()` applies the following stages, in order:

1.  **Cleaning** — Unicode normalization, punctuation and whitespace cleanup
2.  **Diacritic canonicalization** — including apostrophe-variant handling
3.  **Elision expansion** — `n'` → `na`
4.  **Abbreviation / acronym expansion** — `URA` → `Uganda Revenue Authority`
    (case-sensitive, so it runs *before* lowercasing)
5.  **Currency expansion** — `UGX 20,000` → words
6.  **Date / time expansion** — `12/05/2026` → words
7.  **Number expansion** — remaining cardinal numbers → words
    (phone numbers are protected and left untouched)
8.  **Tokenization** — apostrophe-aware
9.  **Lowercasing**
10. **Spelling standardization** — dictionary-based variant correction
11. **Noun-class prefix stripping**
12. **Verb affix stripping**

Stages 4–7 are each individually toggleable (default on) via keyword
arguments on `normalize()`, for callers whose text shouldn't have one of
them applied (e.g. a corpus of raw phone-number logs).

## Example

```python
>>> n.normalize("Nagenda ku 12/05/2026 ne nsasula UGX 20,000.")
"genda ku kkumi na bbiri omwezi ogwokutaano enkumi bbiri mu abiri mu mukaaga ne sasula Uganda shilingi emitwalo ebiri"
```

## Individual components

Every stage is also usable on its own, so you can assemble a custom
pipeline or unit-test a single step:

```python
from normalizer import (
    clean_text,               # cleaner.py
    normalize_diacritics,     # diacritics.py
    expand_elisions,          # contractions.py
    expand_abbreviations,     # abbreviations.py
    expand_currency_to_words, # currency.py
    expand_datetimes,         # datetime.py
    expand_numbers,           # numbers.py
    tokenize,                 # tokenizer.py
    standardize_spelling,     # spelling.py
    NounStripper,             # morphology_nouns.py
    VerbStripper,             # morphology_verbs.py
    tag_tokens,                # codeswitching.py
    has_code_switching,        # codeswitching.py
    handle_social_edge_cases,  # edge_cases.py
)
```

See each module's docstring, or `docs/architecture.md`, for the full
list of exported functions per stage.

### Code-switching detection

Luganda social/news text frequently mixes in English words
("stress", "network", "boss"). This isn't an error to fix — the
normalizer preserves it and can optionally tag or annotate it:

```python
from normalizer import tag_tokens, has_code_switching, annotate_code_switching

tokens = ["omusajja", "abadde", "ne", "stress", "nnyo"]
tag_tokens(tokens)          # per-token LUG / ENG / NUM / PUNCT / UNK tags
has_code_switching(tokens)  # True — has both a LUG and an ENG token
annotate_code_switching("omusajja abadde ne stress nnyo.")
# -> "omusajja abadde ne [ENG]stress[/ENG] nnyo."
```

## Project structure

```
normalizer/
├── __init__.py                  # public API surface
├── pipeline.py                  # normalize() — orchestrates every stage
├── cleaner.py                   # Unicode / punctuation / whitespace cleanup
├── diacritics.py                # diacritic & apostrophe-variant canonicalization
├── contractions.py              # elision expansion (n' -> na)
├── abbreviations.py             # acronym / honorific / cross-language expansion
├── currency.py                  # currency detection & verbalization
├── datetime.py                  # date / time expansion
├── numbers.py                   # number-to-words expansion
├── tokenizer.py                 # apostrophe-aware tokenization
├── spelling.py                  # dictionary-based spelling standardization
├── morphology_nouns.py          # noun-class prefix stripping
├── morphology_verbs.py          # verb affix stripping
├── codeswitching.py             # English/Luganda code-switching detection
├── edge_cases.py                # social-text edge cases (emoji, hashtags, phone numbers)
├── stopwords.py                 # closed-class particle list
├── spelling_dictionary.json     # variant -> canonical spelling mappings
├── abbreviations_dictionary.json# acronym / title / cross-language expansions
└── lexicon_data/                # packaged copies of data/nouns.txt & verbs.txt
    ├── nouns.txt                #   (used by codeswitching.py's LUG lexicon)
    └── verbs.txt

data/                            # canonical source corpora & word lists
docs/architecture.md             # design notes and processing-flow diagram
tests/                           # pytest suite, one file per module
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License