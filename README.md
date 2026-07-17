# Luganda Text Normalizer

A Python library for preprocessing Luganda text for NLP pipelines:
cleaning, elision expansion, abbreviation/acronym expansion, currency
normalization, date/time expansion, number-to-words expansion,
tokenization, dictionary-based spelling standardization, noun/verb
morphology stripping, and English–Luganda code-switching detection.

> Status: actively developed. See [`docs/architecture.md`](docs/architecture.md)
> for the full design rationale, module inventory, and known limitations.

## Install

From the project root, editable install (recommended for development):

```bash
pip install -e .
# with dev/test dependencies:
pip install -e ".[dev]"
```

Requires Python ≥ 3.9. Depends on `nltk>=3.8` (see `requirements.txt`).

## Quick start

```python
import normalizer

normalizer.normalize("Nasasula UGX 50,000 nga 16/07/2026 essaawa 07:00.")
```

Or use individual stages directly, without the full pipeline:

```python
from normalizer import number_to_words, expand_currency_to_words, expand_abbreviations

number_to_words(45)                      # -> "amakumi ana mu ttaano"
expand_currency_to_words("Ekiguzibwa $10 nedda.")
                                          # -> "Ekiguzibwa ddoola kkumi nedda."
expand_abbreviations("URA basoma tax.")  # -> "Uganda Revenue Authority basoma tax."
```

## What it does

The pipeline covers ten preprocessing capabilities, each implemented
in its own module so you can use just the pieces you need:

| # | Capability | Module | Example |
|---|---|---|---|
| 1 | Unicode normalization | `cleaner` | NFC-normalizes text, fixes stray control characters |
| 2 | Lowercasing | `pipeline` | applied after tokenization, before spelling lookup |
| 3 | Punctuation cleanup | `cleaner` | standardizes quotes/dashes, collapses repeated punctuation |
| 4 | Number expansion | `number_words` | `25` → `amakumi abiri mu ttaano` |
| 5 | Date/time expansion | `datetime_expand` | `16/07/2026` → `Lwakutaano, olunaku 16 mu mwezi gwa Julaayi, mu mwaka 2026` |
| 6 | Currency normalization | `currency` | `50,000/=` → `UGX 50,000`, or fully spelled out |
| 7 | Abbreviation expansion | `abbreviations` | `URA` → `Uganda Revenue Authority`, `Dr` → `Dokita` |
| 8 | Spelling correction | `spelling` | dictionary-based variant → canonical spelling |
| 9 | Morphological normalization | `morphology_nouns`, `morphology_verbs` | strips noun-class and verb affixes to a root |
| 10 | Code-switching handling | `edge_cases`, `code_switching` | preserves embedded English rather than mangling it, and can tag/detect it on request |

See [`docs/architecture.md`](docs/architecture.md) for the full
pipeline order, the reasoning behind that order, and every module's
documented assumptions and limitations.

## Full pipeline

```python
normalizer.normalize(
    text,
    expand_abbrevs=True,       # URA -> Uganda Revenue Authority, Dr -> Dokita, etc.
    expand_currency=True,      # UGX 50,000 / $10 / 50,000/= -> spelled-out amounts
    expand_dates_times=True,   # 16/07/2026, 07:00 -> Luganda date/time words
    expand_nums=True,          # plain cardinal numbers -> Luganda words
)
```

Each expansion stage can be turned off independently if it's not right
for your input (e.g. a corpus of raw phone-number logs).

`code_switching`'s tagging/annotation functions are **not** part of
the default `normalize()` output — they're an analysis tool you call
directly (`tag_tokens`, `has_code_switching`, `annotate_code_switching`)
when you want to inspect where English and Luganda mix, rather than a
step that rewrites your text.

## Running the tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

As of this writing: **197 passing tests** across cleaning, diacritics,
edge cases, abbreviations, currency, date/time, numbers, tokenization,
spelling, morphology, code-switching, and the end-to-end pipeline.

(Two files, `tests/test_morphology_nouns.py` and
`tests/test_morphology_verbs.py`, are standalone scripts rather than
pytest modules — run them directly with `python tests/test_morphology_nouns.py`.
Neither passes its full internal expectation table (pre-existing
class-disambiguation ambiguities, plus one intentional table entry now
stale after this update's numeral fix) — see
[`docs/architecture.md`](docs/architecture.md#2-module-status) for the
full explanation.)

## Known limitations

Every module documents its own assumptions and limitations inline
(read the module docstrings), but the headline ones:

- **Numbers**: no confirmed Luganda word for magnitudes ≥ 1,000,000 —
  `number_words.number_to_words` raises `NumberTooLargeError` rather than
  guess one.
- **Dates/times**: the morning/afternoon/evening/night qualifier
  wording and boundaries are a best-effort default, not a
  native-speaker-confirmed standard.
- **Currency**: only UGX and USD are covered.
- **Dictionaries** (`spelling_dictionary.json`,
  `abbreviations_dictionary.json`) are intentionally small, vetted
  seed sets — extend them with confirmed entries only, not guesses.
- **Code-switching**'s English word list is a small curated set
  (~120 words), not a general-purpose language identifier.

Full detail, plus the reasoning behind the pipeline's stage ordering,
is in [`docs/architecture.md`](docs/architecture.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT — see [`LICENSE`](LICENSE).
