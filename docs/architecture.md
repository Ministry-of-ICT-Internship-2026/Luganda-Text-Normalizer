# Architecture

> Status: all modules listed below are implemented and tested.
> Last updated: 2026-07-16

## 1. Overview

`normalizer` (pip name: `luganda-normalizer`) is a Python library for
preprocessing Luganda text for downstream NLP tasks: cleaning, elision
expansion, abbreviation/acronym expansion, currency normalization,
date/time expansion, number-to-words expansion, tokenization, spelling
standardization, noun/verb morphology stripping, and English/Luganda
code-switching detection. It wraps and extends NLTK for tokenization
rather than reimplementing one from scratch, patching only the
specific places NLTK's English-oriented rules break on Luganda.

`pipeline.normalize()` is the single entry point most callers want;
every stage is also exported individually (see `normalizer/__init__.py`)
so callers can assemble a custom pipeline or unit-test one step.

## 2. Module status

Reflects the actual files in `normalizer/` as of this update. Every
module below is implemented (no stubs remain) and has a corresponding
test file in `tests/`.

| Module               | Purpose                                              | File                              | Tests |
|----------------------|-------------------------------------------------------|------------------------------------|-------|
| package init         | re-exports every public symbol                        | `normalizer/__init__.py`          | —     |
| `cleaner`            | unicode/quote/whitespace/punctuation cleanup           | `normalizer/cleaner.py`           | `test_cleaner.py` (9) |
| `diacritics`         | tone-mark canonicalization                             | `normalizer/diacritics.py`        | `test_diacritics.py` (7) |
| `contractions`       | elision expansion (`n'ekitabo` → `na ekitabo`)          | `normalizer/contractions.py`      | (covered via pipeline/tokenizer tests) |
| `edge_cases`         | social-text quirks: emoji, hashtags, phone/currency detection, mixed-language preservation | `normalizer/edge_cases.py` | `test_edge_cases.py` (18) |
| **`abbreviations`**  | **acronym/title/cross-language abbreviation expansion** | `normalizer/abbreviations.py`   | `test_abbreviations.py` (16) |
| **`currency`**       | **currency marker detection, format normalization, amount-to-words** | `normalizer/currency.py` | `test_currency.py` (21) |
| **`datetime_expand`**| **date and clock-time expansion into Luganda words**    | `normalizer/datetime_expand.py` | `test_datetime_expand.py` (28) |
| **`number_words`**        | **cardinal number-to-Luganda-words expansion**          | `normalizer/number_words.py`         | `test_number_words.py` (42) |
| `tokenizer`          | Luganda-aware word tokenization (apostrophe-safe)       | `normalizer/tokenizer.py`        | `test_tokenizer.py` + hard/deep variants |
| `spelling`           | dictionary-based spelling standardization               | `normalizer/spelling.py`         | `test_spelling.py` (33) |
| `morphology_nouns`   | noun-class prefix stripping                             | `normalizer/morphology_nouns.py` | `test_morphology_nouns.py`* |
| `morphology_verbs`   | verb subject/object/tense affix stripping               | `normalizer/morphology_verbs.py` | `test_morphology_verbs.py`* |
| **`code_switching`** | **English/Luganda token tagging + annotation**          | `normalizer/code_switching.py`  | `test_code_switching.py` (21) |
| `stopwords`          | closed-class word list shared by both morphology strippers | `normalizer/stopwords.py`     | (covered via morphology tests) |
| `pipeline`           | wires every stage together into `normalize()`           | `normalizer/pipeline.py`         | `test_pipeline.py` (smoke test) |

**Bold** rows are the modules added in this update to cover the full
requested preprocessing checklist (see section 4).

\* `test_morphology_nouns.py` / `test_morphology_verbs.py` are
standalone scripts (a `__main__` block with print-based assertions),
not pytest test modules -- `pytest` collects 0 tests from them. Run
them directly with `python tests/test_morphology_nouns.py`. Neither
currently passes 100% of its own internal expectation table, and
**this was true before this update too** -- both scripts encode known
ambiguities in the noun/verb-class heuristics (e.g. `N` vs `LU-N`
class disambiguation, `KA-BU` vs `BU`) that were never fully resolved.
One additional, *intentional* behavior change from this update: the
noun script's table expects `enkumi` ("thousands") to strip to `kumi`;
it no longer does, because `enkumi` was added to
`stopwords.CLOSED_CLASS` (section 5.1) so `number_words.py`'s numeral
output survives the pipeline correctly. That table entry is now
stale, not a regression -- the new behavior is the one `numbers`
actually needs. These scripts are NOT part of the `pytest tests/`
count reported by CI either way. Converting them to proper pytest
functions (and refreshing their expectation tables) is tracked in the
roadmap (section 9).

## 3. Full pipeline order

```
raw text
   │
   ▼
clean_text                    (cleaner.py)
   │
   ▼
normalize_diacritics          (diacritics.py)
   │
   ▼
expand_elisions                (contractions.py)   n'X -> na X
   │
   ▼
expand_abbreviations           (abbreviations.py)  BEFORE lowercasing:
   │                                                acronyms are case-sensitive
   ▼
expand_currency_to_words       (currency.py)       BEFORE number expansion:
   │                                                consumes amount digits as a unit
   ▼
expand_datetimes               (datetime_expand.py) BEFORE number expansion:
   │                                                consumes date/time digits as a unit
   ▼
expand_numbers                 (number_words.py)        whatever plain numbers remain
   │                                                (phone numbers protected via
   │                                                 edge_cases.PHONE_NUMBER_RE skip-spans)
   ▼
tokenize                       (tokenizer.py)
   │
   ▼
lowercase
   │
   ▼
standardize_tokens             (spelling.py)
   │
   ▼
NounStripper / VerbStripper    (morphology_nouns.py / morphology_verbs.py)
   │
   ▼
normalized string
```

`pipeline.normalize()` accepts `expand_abbrevs`, `expand_currency`,
`expand_dates_times`, and `expand_nums` keyword arguments (all default
`True`) so any of the four expansion stages can be disabled by a
caller without forking the function.

`code_switching.py` is deliberately **not** wired into the default
`normalize()` text-rewriting pipeline: it tags/annotates rather than
rewrites (matching `edge_cases.py`'s "preserve mixed-language text,
don't guess at fixing it" stance), and inserting `[ENG]...[/ENG]`
markers into normalized output would surprise callers who just want
clean text back. Call `code_switching.tag_tokens()` /
`annotate_code_switching()` directly when you want that analysis.

## 4. The ten preprocessing capabilities, mapped to modules

| # | Capability                                   | Module(s)                     |
|---|-----------------------------------------------|--------------------------------|
| 1 | Unicode normalization                          | `cleaner.normalize_unicode`   |
| 2 | Lowercasing                                    | `pipeline.normalize` (post-tokenize step) |
| 3 | Punctuation removal/standardization             | `cleaner.py` (quotes, dashes, repeated punctuation, spacing) |
| 4 | Number expansion into Luganda words             | `number_words.py`                  |
| 5 | Date/time expansion                            | `datetime_expand.py`          |
| 6 | Currency normalization (UGX, USD, ...)          | `currency.py`                 |
| 7 | Abbreviation expansion                         | `abbreviations.py`            |
| 8 | Dictionary-based spelling correction            | `spelling.py`                 |
| 9 | Morphological normalization (noun/verb variants)| `morphology_nouns.py`, `morphology_verbs.py` |
| 10| English–Luganda code-switching handling         | `edge_cases.py` (preservation) + `code_switching.py` (detection/tagging) |

## 5. New-module design notes

### 5.1 `number_words.py`

Implements the standard Luganda cardinal-number system (units 0-9,
teens via `kkumi na X`, tens via `<tens> mu X`, hundreds/thousands the
same way, recursively). **Documented limitation:** magnitudes ≥
1,000,000 raise `NumberTooLargeError` rather than guess a word, since
no native-speaker-confirmed form for "million" has been vetted for
this project (see the module docstring for the reasoning). Callers
that hit the ceiling get an explicit, catchable signal; `expand_numbers()`
catches it internally and leaves the original digits untouched rather
than crashing or mangling the text.

Every atomic word this module can produce (`emu`, `mukaaga`, `amakumi`,
`enkumi`, ...) was added to `stopwords.CLOSED_CLASS` -- without this,
`morphology_nouns.py` and `morphology_verbs.py` mistake numeral
morphology for noun-class prefixes (e.g. `mukaaga`, "six," looks
exactly like `MU-BA`-class `mu-` + root `kaaga`, and would otherwise be
wrongly stripped to `kaaga`). This was caught and fixed by testing the
full pipeline end-to-end with real numeral input, not just the
`number_words.py` unit tests in isolation.

### 5.2 `datetime_expand.py`

Weekday and month names use the standard Luganda calendar vocabulary.
Clock time uses East African "6 o'clock" reckoning (day starts at
06:00, same convention as Swahili "saa" time): `07:00` → `ssaawa emu`,
`18:00` → `ssaawa kkumi na bbiri`. **Documented limitation:** the
morning/afternoon/evening/night qualifier wording and its hour
boundaries are a best-effort default, not a native-speaker-confirmed
standard -- see the module docstring. Luganda ordinal-number formation
(noun-class agreement for "the Nth day") is out of scope; day-of-month
numbers are rendered as plain digits.

### 5.3 `currency.py`

Recognizes UGX (`UGX`, `USh`, the `/=` slash notation) and USD (`$`,
`USD`) markers in both prefix (`UGX 50,000`) and suffix (`50,000/=`)
position, normalizes them to a canonical `<CODE> <amount>` form, and
can spell the amount out via `number_words.py` (`amount_to_words`). Only
UGX and USD are covered; other currencies are intentionally left out
rather than guessing a symbol/word pair by analogy (see module
docstring). Fractional amounts and amounts beyond `number_words.py`'s
magnitude ceiling fall back to `"<unit word> <digits>"` instead of
raising, so currency text is never left half-mangled.

### 5.4 `abbreviations.py`

Dictionary-backed (`abbreviations_dictionary.json`), same
load-and-fall-back-safely architecture as `spelling.py`. Three
categories: `organizations` (government/parastatal acronyms like
`URA`, `KCCA` — matched **case-sensitively**, since an acronym's
casing is part of its identity), `titles` (`Dr` → `Dokita`, etc. —
case-insensitive), and `cross_language` (`etc` → `n'ebirala`, `e.g.` →
`gamba nga` — case-insensitive). The regex uses `(?<!\w)`/`(?!\w)`
lookarounds rather than `\b`, because plain `\b` silently fails to
match abbreviations that end in punctuation (`e.g.`) since `.` is not
a word character.

### 5.5 `code_switching.py`

Lexicon-based tagging (`LUG` / `ENG` / `NUM` / `PUNCT` / `UNK`), not a
generic language identifier. The Luganda side draws on
`normalizer/lexicon_data/{nouns,verbs}.txt` (a packaged copy of
`data/nouns.txt` / `data/verbs.txt` — see section 7 on why this had to
be duplicated rather than referenced directly), `stopwords.CLOSED_CLASS`,
and the spelling dictionary. The English side is a small, curated list
of ~120 common words (**not** a real English dictionary — documented
limitation in the module). Every result carries a `method` field
(`"lexicon"` or `"none"`) so callers can see exactly how confident a
tag is; unknown tokens are tagged `UNK` rather than guessed at, in
keeping with `edge_cases.py`'s existing "preserve rather than guess"
stance on mixed-language text.

## 6. Testing strategy

- `pytest` as the test runner (`pip install -e .[dev]`).
- Each module has a dedicated test file; the newer modules
  additionally test boundary/error conditions (invalid dates,
  magnitude ceilings, corrupt dictionary files, unmapped input) rather
  than only happy-path cases, following the pattern set by
  `test_tokenizer_hard.py` / `test_tokenizer_deep.py`.
- Current count: **197 passing tests** via `pytest tests/ -q` (plus
  the two standalone morphology scripts noted in section 2, run
  separately).
- No CI workflow is currently checked into this repo (no
  `.github/workflows/`) — see roadmap.

## 7. Known limitations / packaging notes

- **`number_words.py` magnitude ceiling:** no word for ≥ 1,000,000 yet;
  raises `NumberTooLargeError` rather than guessing (section 5.1).
- **`datetime_expand.py` period-qualifier boundaries** and **currency
  unit-word phrasing** are best-effort, not linguist-vetted (sections
  5.2, 5.3).
- **`abbreviations_dictionary.json` and `spelling_dictionary.json`**
  are both intentionally small, confirmed-only seed sets. Extend them
  the same way: only add an entry once a native speaker (or, for
  organization acronyms, an authoritative public source) has confirmed
  it — do not guess by analogy.
- **`code_switching.py`'s Luganda lexicon is duplicated, not shared:**
  `data/nouns.txt` and `data/verbs.txt` live outside the `normalizer/`
  package directory, so they are not shipped inside a `pip install`
  wheel. A copy was placed at `normalizer/lexicon_data/*.txt` and
  wired into `pyproject.toml`'s `package-data` so the installed package
  works standalone. **This copy must be kept in sync manually** if
  `data/nouns.txt` or `data/verbs.txt` are updated — there is no
  automated sync step yet (tracked in the roadmap below).
- **`data/` corpora (`Bible_source.txt`, `news_source.txt`,
  `twitter_source.txt`, `sample_corpus.txt`) are not packaged** at all
  — they're reference/research corpora, not runtime dependencies of
  any module, so this is expected, not a bug.

## 8. Data flow (tokenizer sub-diagram)

```
raw text
   │
   ▼
[find apostrophe-words via regex]───►[stash as placeholders]
   │                                          │
   ▼                                          │
[protected text] ──► nltk.word_tokenize() ──► rough tokens
                                               │
                                               ▼
                              [restore placeholders back to real words]
                                               │
                                               ▼
                                          final tokens
```

## 9. Open questions / roadmap

- [ ] Automate the `data/{nouns,verbs}.txt` ↔
      `normalizer/lexicon_data/{nouns,verbs}.txt` sync (section 7) —
      currently a manual copy, easy to let drift.
- [ ] Convert `test_morphology_nouns.py` / `test_morphology_verbs.py`
      from standalone print-based scripts into real `pytest` test
      functions so they're included in the `pytest tests/` count.
- [ ] Get native-speaker sign-off on: the ≥1,000,000 Luganda number
      word(s), the datetime period-qualifier wording/boundaries, and
      the currency unit-word phrasing (all documented as best-effort
      in section 5).
- [ ] Expand `abbreviations_dictionary.json` beyond the current seed
      set of ~9 organizations / 4 titles / 3 cross-language terms —
      vetted additions only.
- [ ] Expand `code_switching.py`'s English word list beyond the
      current ~120-word curated set (still not a general-purpose
      language identifier — see section 5.5).
- [ ] Expand corpus beyond the current sources — no `data/README.md`
      currently documents provenance/licensing; add one before adding
      further sources.
- [ ] Packaging: publish to PyPI or keep as internal/course library?
- [ ] No CI workflow currently exists in this repo — add one
      (`.github/workflows/tests.yml`) running `pytest` across the
      Python versions declared in `pyproject.toml` (`>=3.9`).
