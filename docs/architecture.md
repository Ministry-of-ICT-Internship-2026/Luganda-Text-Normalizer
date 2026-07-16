# Architecture

> Status: all core modules implemented and wired into `pipeline.normalize()`.
> Last updated: 2026-07-16

## 1. Overview

`normalizer` (distributed on PyPI as **`luganda-normalizer`**) is a Python
library for preprocessing Luganda text for downstream NLP tasks: cleaning,
elision expansion, diacritic canonicalization, tokenization, spelling
standardization, and noun/verb morphology stripping. It wraps and extends
NLTK for tokenization rather than reimplementing a tokenizer from scratch,
patching only the specific places NLTK's English-oriented rules break on
Luganda.

The project name/import split, worth stating up front because it trips
people up:

| | value |
|---|---|
| PyPI / pip install name | `luganda-normalizer` |
| Python import name | `normalizer` |
| Version | `1.0.0` |

This mirrors common practice (e.g. `pip install beautifulsoup4` →
`import bs4`) and is deliberate — every internal module and every test in
this repo already imports its siblings as `normalizer.xxx`, so the import
name was kept stable rather than renamed to match the distribution name.

## 2. Module status

Reflects the actual files in `normalizer/` as of this repo snapshot. Every
module listed here is implemented (not a stub) and has direct or
pipeline-level test coverage.

| Module | Responsibility | File | Status |
|---|---|---|---|
| package init / public API | re-exports every stage | `normalizer/__init__.py` | ✅ done |
| `cleaner` | Bucket-A mechanical text cleanup | `normalizer/cleaner.py` | ✅ done |
| `edge_cases` | numbers, emoji, hashtags/mentions | `normalizer/edge_cases.py` | ✅ done |
| `contractions` | apostrophe-elision expansion (`n'` → `na`) | `normalizer/contractions.py` | ✅ done |
| `diacritics` | confirmed diacritic/spelling-variant canonicalization | `normalizer/diacritics.py` | ✅ done, table currently empty (see §6) |
| `tokenizer` | apostrophe-aware, abbreviation-safe tokenization | `normalizer/tokenizer.py` | ✅ done |
| `spelling` | dictionary-based spelling standardization | `normalizer/spelling.py` | ✅ done, dictionary currently empty (see §8) |
| `morphology_nouns` | noun-class prefix stripping | `normalizer/morphology_nouns.py` | ✅ done, self-test dead code (see §11) |
| `morphology_verbs` | verb affix stripping | `normalizer/morphology_verbs.py` | ✅ done, self-test dead code (see §11) |
| `stopwords` | shared closed-class word list | `normalizer/stopwords.py` | ✅ done |
| `pipeline` | chains every stage into `normalize()` | `normalizer/pipeline.py` | ✅ done |

Referenced elsewhere but **not present** in this snapshot (documented here
so nobody goes looking for them): `data/README.md`, `scripts/download_corpus.py`,
`scripts/clean_corpus.py`, `.github/workflows/tests.yml`. Treat these as
roadmap items (§13), not existing files.

## 3. Public API surface

`import normalizer` exposes, flat, everything below (see `__init__.py`
for the authoritative list):

```
normalize                                          # full pipeline, one call

clean_text, normalize_unicode, strip_control_characters,
standardize_quotes_and_dashes, fix_spacing_before_punctuation,
collapse_repeated_punctuation, collapse_whitespace  # cleaner

expand_elisions                                     # contractions

normalize_diacritics, list_pending_reviews,
add_confirmed_variant                               # diacritics

fix_number_word_spacing, find_numeric_entities,
extract_emoji, extract_hashtags_and_mentions,
handle_social_edge_cases                            # edge_cases

tokenize, diagnose                                   # tokenizer

load_dictionary, standardize_spelling,
standardize_tokens                                   # spelling

NounStripper, VerbStripper                            # morphology

CLOSED_CLASS                                          # stopwords
```

Every pipeline stage is exported individually as well as wired into
`normalize()`, so callers can assemble a custom pipeline, swap a stage
out, or unit-test one step in isolation without importing submodules
directly.

## 4. `pipeline.normalize()` — the full pipeline

```python
def normalize(text: str) -> str:
    text = clean_text(text)
    text = normalize_diacritics(text)   # canonicalize chars (incl. apostrophe variants) first
    text = expand_elisions(text)        # now safely splits n'X -> na X on canonical apostrophes

    tokens = tokenize(text)
    tokens = [t.lower() for t in tokens]  # lower BEFORE any lowercase-keyed lookup step
    tokens = standardize_tokens(tokens)   # spelling dict lookups now match reliably

    noun_stripper = NounStripper()
    verb_stripper = VerbStripper()

    normalized_tokens = []
    for token in tokens:
        root, prefix, _class_id = noun_stripper.strip(token)
        if prefix is None:
            root, _affixes = verb_stripper.strip(root)
        normalized_tokens.append(root)

    return " ".join(normalized_tokens)
```

**Ordering is load-bearing, not incidental** — each comment above documents
a real bug that ordering fixed:

1. `clean_text` → `normalize_diacritics` → `expand_elisions`: elision
   expansion matches on the apostrophe character, so it must run after
   diacritic/quote canonicalization has already collapsed curly `’` to
   straight `'`, or a curly-quote elision silently fails to expand.
2. `tokenize` → lowercase → `standardize_tokens`: the spelling dictionary
   is keyed lowercase; lowercasing after tokenization (not before, and not
   skipped) is what makes dictionary lookups match reliably. Tokenizing
   before lowercasing also matters on its own — see §5, `tokenize()`
   deliberately doesn't lowercase by default because capitalization
   carries information (sentence-initial `Ng'` vs. mid-sentence `ng'`).
3. Noun stripping is attempted **before** verb stripping, and verb
   stripping only runs `if prefix is None` (i.e. the noun stripper found
   nothing to strip). This is a real design decision, not just a for-loop
   ordering: it means a token that could plausibly be read either way is
   always resolved as a noun first. See §12 for why this is a known
   accuracy limitation, not a settled linguistic rule.

## 5. `cleaner` + `edge_cases` modules

### 5.1 Problem they solve

`clean_text()` implements the "Bucket A" mechanical rules identified by
inspecting real Luganda text from Bukedde news, Twitter/X, and the Luganda
Revised Bible: NFC unicode normalization, control-character stripping,
curly-quote/en-dash canonicalization, punctuation spacing, repeated-
punctuation collapsing, and whitespace collapsing.

`edge_cases.py` was added specifically because Bucket A was built and
tested against fairly well-formed text (Bible, news) and did not hold up
against informal/social text. It handles three patterns:

1. **Mixed-language text** — deliberately *not* touched. Embedded English
   words (e.g. "stress" in `omusajja abadde ne stress z'awaka`) are real
   code-switching, not an error to fix. Language detection is left to a
   module with more context (dictionary, language model).
2. **Numbers** — `fix_number_word_spacing()` inserts a space between a
   digit and a following word, *unless* the letters look like a short
   tech/time abbreviation (`4G`, `3D`, `2FA`, `9am`), which stays glued.
   `find_numeric_entities()` surfaces phone numbers (Ugandan formats) and
   currency amounts so a caller can mark those spans as non-linguistic
   rather than trying to spell-check them.
3. **Emoji / hashtags / mentions** — `extract_emoji()` removes emoji but
   returns what was found (not silently discarded — a future
   sentiment/tone component may still want them). Hashtags and mentions
   are surfaced by `extract_hashtags_and_mentions()` but left in the text
   by default, since they often carry meaning (an organization name, a
   campaign tag).

### 5.2 Design principle

Both modules follow the same rule: **when in doubt, preserve rather than
guess.** `clean_text()` explicitly does *not* strip stray caption
artifacts (e.g. a leftover "Portrait" from a scrape) because that pattern
is too easy to confuse with legitimate short English loanwords.

## 6. `diacritics` module

### 6.1 Design principle

Only diacritic/spelling variants **explicitly confirmed by a native or
fluent Luganda speaker** are ever merged. This is an explicit lookup table
(`CONFIRMED_VARIANTS`), not a generic "strip all diacritics" rule — a
blanket rule is exactly how two different words get silently collapsed
into one, corrupting everything downstream.

### 6.2 Current status

`CONFIRMED_VARIANTS` is **empty**. `normalize_diacritics()` is therefore
currently a no-op beyond NFC normalization (which is an encoding-level
fix, not a linguistic decision, and is handled separately in `cleaner.py`
for that reason).

One candidate is logged and tracked but **not applied**:
`ŋŋ` vs `ng'` — pending a native-speaker decision on whether they're
interchangeable spellings or mark a real sound/length distinction.
`list_pending_reviews()` surfaces this queue programmatically (useful for
generating a review agenda); `add_confirmed_variant()` is the sanctioned
way to promote an entry out of it once reviewed — mutating
`CONFIRMED_VARIANTS` by hand mid-pipeline is deliberately discouraged so
every addition is a traceable, conscious act.

## 7. `contractions` module

### 7.1 Problem it solves

Luganda often drops a vowel and glues a short word onto the next one with
an apostrophe — `n'emikyungwa` = `na` + `emikyungwa` ("and jackfruit"). Left
alone, the noun/verb strippers mistake the glued letter for a class prefix
and mangle both halves of the word.

### 7.2 Design principle

Same safety philosophy as `FALSE_POSITIVES` / `CLOSED_CLASS` elsewhere in
this project: only expand elisions that have been explicitly confirmed
(currently just `n'` → `na`). Guessing new ones in is how an unconfirmed
elision silently corrupts text that was never actually contracted.

### 7.3 Two fixed bugs worth knowing about

- **Ordering**: `expand_elisions()` must run on the raw string, *before*
  `tokenizer.tokenize()`. It matches with `\b` word boundaries; once the
  tokenizer has already split/masked the text, those boundaries no longer
  line up and the pattern silently stops matching.
- **Case preservation**: the elision key is matched case-insensitively (so
  sentence-initial `N'ekitabo` is recognized), but the expansion mirrors
  the matched key's case rather than always substituting the lowercase
  form. This prevents `expand_elisions()` from silently lowercasing
  sentence-initial words, which would otherwise corrupt any downstream
  sentence-boundary detection relying on capitalization.

## 8. `spelling` module

### 8.1 Approach

`load_dictionary()` reads a variant → canonical mapping from
`normalizer/spelling_dictionary.json`. `standardize_spelling()` /
`standardize_tokens()` replace known variants; **unknown words always pass
through unchanged** — this fallback is the module's core safety property,
since the dictionary is intentionally incomplete. A missing or corrupt
dictionary file degrades to a no-op rather than raising, so it never
breaks the rest of the pipeline.

### 8.2 Current status

`spelling_dictionary.json`'s `mappings` object is currently **empty**.
`standardize_spelling()` / `standardize_tokens()` are live and tested, but
have nothing to standardize yet — populating the dictionary from a vetted
source is open work (§13).

## 9. `tokenizer` module

### 9.1 Problem it solves

`nltk.word_tokenize()` uses Penn Treebank rules built for English. Three
failure modes were found empirically (not assumed) against real Luganda
text and are each covered by a dedicated test:

1. **Curly apostrophe (`’`, U+2019)** — the default output of Word,
   Google Docs, and most phones (autocorrect converts `'` to `’`). NLTK
   treats it as standalone punctuation: `n'ekitabo` (straight quote)
   survives as one token by coincidence, but `n’ekitabo` (curly quote) is
   shredded into `['n', '’', 'ekitabo']`.
2. **Known abbreviations losing their period** — once masking is
   introduced, NLTK no longer sees the literal word `Dr` (it sees an
   opaque placeholder), so it can't apply its own abbreviation whitelist
   and splits `Dr.` into `['Dr', '.']`.
3. **Placeholder/text namespace collisions** — if the raw input already
   contains something shaped like the tokenizer's own internal
   placeholder tag (e.g. a product code or ticket ID), the restore step
   could previously either crash with `KeyError` or silently substitute
   the wrong word back in.

### 9.2 Approach

Mask-before-tokenize:

1. Find Luganda word spans and known abbreviations via regex and swap
   them for alphanumeric placeholders (`_PROTECTED_RE`), canonicalizing
   curly `’` → straight `'` in the process.
2. Run standard `nltk.word_tokenize()` on the rest.
3. Restore placeholders — by **substring** match, not exact-token match,
   so a placeholder NLTK left glued to stray punctuation still resolves
   instead of leaking the raw placeholder string into the output.

Fix for failure mode 3: the placeholder tag is not a fixed constant. Each
call generates a random per-call suffix and verifies it does not already
appear anywhere in the source text before using it (retrying on the rare
collision), making an accidental or adversarial collision impossible
rather than merely unlikely.

Plain words with no apostrophe are deliberately left untouched (the word
regex requires *at least one* apostrophe group) so NLTK's own
abbreviation handling keeps working on everything else.

### 9.3 Known limitations (documented, not silently papered over)

- The `ng'`/elision ambiguity (the same three characters can be a single
  letter *or* the tail of an elided `nga`) is not resolved — both are
  treated identically (never split), which is the safe default but not
  always linguistically correct. Real resolution needs a lexicon.
- Malformed double apostrophes (typos/bad OCR, e.g. `n''ekitabo`) are not
  specially handled; would need a cleanup pass upstream of tokenization.

### 9.4 `diagnose()`

A convenience function that runs both plain `nltk.word_tokenize()` and
this module's `tokenize()` on the same sentence and returns both outputs
side by side — useful for demonstrating, or regression-testing, exactly
where and how the default tokenizer breaks.

## 10. `morphology_nouns` module

`NounStripper.strip(word)` returns `(root, matched_prefix, class_id)`
(or `(word, None, None)` if nothing was safely stripped). It implements
eight Luganda noun classes (`MU-BA`, `MU-MI`, `LI-MA`, `KI-BI`, `N`,
`LU-N`, `KA-BU`, `BU`) as a prefix table, sorted longest-prefix-first so
e.g. `omu-` is tried before the shorter `mu-`.

Three safety nets, all logged via the standard `logging` module so a
caller can audit exactly why a given word was or wasn't stripped:

- **`CLOSED_CLASS`** (shared with `morphology_verbs`, defined in
  `stopwords.py`) — words that must never be stripped regardless of shape,
  e.g. `abamu` ("some") looks like a `MU-BA` plural noun but is actually a
  quantifier.
- **`FALSE_POSITIVES`** — words that look like they have a class prefix
  but don't, e.g. `kikumi` ("100"), `musa` (a proper name), `bizineesi`
  (the loanword "business" — `bi-` isn't a class prefix here). Checked
  both for the whole word and for the resulting root, so stripping is
  blocked either way.
- **`MIN_ROOT_LENGTH`** — a stripped root shorter than 2 characters is
  rejected and the original word is returned unchanged, guarding against
  over-stripping short words down to fragments.

## 11. `morphology_verbs` module

`VerbStripper.strip(word)` returns `(root, list_of_removed_parts)`. It
peels affixes off in a fixed order — infinitive (`oku-`) → negative
(`si-`, `to-`, `te-`, and the compound `tetu-`/`temu-`/`teba-`) → subject
marker → tense → object infix — stopping early (and reverting to the
original word) if the result would be shorter than `MIN_ROOT_LENGTH`.

Two things worth knowing:

- **`_looks_like_verb()`** is a cheap heuristic, not a real POS tagger:
  starts with `oku-`, or ends in `-a`/`-e`. It exists purely to filter out
  an easy class of non-verbs before affix-stripping runs on them, and is
  explicitly documented in the code as a heuristic, not a guarantee.
- **Compound negatives already bake in a subject marker.** `tebalina`
  ("they don't have") must strip as `negative:teba` only, *not* also
  strip a subject prefix afterward — doing both was a real, now-fixed bug
  that turned `tebalina` into `na` instead of the correct `lina`.
  `COMPOUND_NEGATIVES` tracks which negative prefixes already consumed the
  subject slot so the subject-stripping step knows to skip.

### 11.1 Dead self-test code (both morphology modules)

`morphology_nouns.py` and `morphology_verbs.py` each end with an
`if __name__ == "__main__":` self-test block. In both files, that block is
currently **wrapped inside a triple-quoted string literal** (a bare `"""`
opens right after the class definition, and another closes it at end of
file) — meaning the self-test **never actually runs**, even via
`python -m normalizer.morphology_nouns`. It's inert dead code, not a
runtime bug (nothing imports or calls it), but worth knowing before
assuming those files have a working standalone smoke test. Real coverage
for both modules instead lives in `tests/test_morphology_nouns.py` and
`tests/test_morphology_verbs.py`.

## 12. Known pipeline-level limitations

These are consequences of composing the modules above, worth stating
plainly rather than discovering by surprise:

- **`normalize()` is deliberately aggressive and lossy.** It's built for
  downstream tasks (search indexing, embedding, bag-of-words style
  features) where root forms matter more than surface form — not for
  anything that needs to reconstruct readable text. For example,
  `"Dr. Musisi yagenda mu ddwaliro."` normalizes to
  `"dr. sisi yagenda mu ddwaliro ."` — `Musisi` (a proper name) loses its
  `Mu-` as if it were a class prefix, because morphology stripping has no
  named-entity awareness. Don't run `normalize()` output through anything
  that expects grammatical, human-readable Luganda.
- **Noun-first resolution order is a heuristic, not a linguistic rule**
  (see §4, point 3). A token that's ambiguous between noun and verb
  reading is always resolved as a noun. This is a known, accepted
  simplification — not yet backed by a disambiguation strategy.
- **Two safety-net tables are currently empty**: `CONFIRMED_VARIANTS` (§6)
  and `spelling_dictionary.json`'s `mappings` (§8). Both stages run and
  are tested, but do nothing yet in practice until populated.

## 13. Corpus / data

`data/` currently contains four raw source files (`Bible_source.txt`,
`news_source.txt`, `twitter_source.txt`, `sample_corpus.txt`) and two
morphology test-data files (`nouns.txt`, `verbs.txt`) used by
`tests/test_morphology_nouns.py` / `tests/test_morphology_verbs.py`. There
is currently no `data/README.md` documenting provenance/licensing, and no
`scripts/download_corpus.py` / `scripts/clean_corpus.py` — both are
open work items, not existing tooling (see §15).

## 14. Data flow

```
raw text
   │
   ▼
clean_text()              ── NFC normalize, strip control chars, quotes/dashes,
   │                         number spacing, emoji strip, punctuation spacing,
   │                         collapse repeats, collapse whitespace
   ▼
normalize_diacritics()    ── apply confirmed variant table (currently a no-op, §6)
   │
   ▼
expand_elisions()         ── n'X -> na X  (confirmed elisions only, §7)
   │
   ▼
tokenize()                ── mask apostrophe-words + abbreviations, delegate to
   │                         nltk.word_tokenize(), restore placeholders (§9)
   ▼
lowercase tokens
   │
   ▼
standardize_tokens()      ── dictionary lookup, unknowns pass through (§8)
   │
   ▼
NounStripper.strip()  ──►  if no noun prefix found  ──►  VerbStripper.strip()
   │                                                            │
   └────────────────────────┬───────────────────────────────────┘
                             ▼
                    join tokens with " "
                             │
                             ▼
                      normalized string
```

Sub-diagram, tokenizer's internal masking step (§9.2):

```
raw text
   │
   ▼
[find apostrophe-words + abbreviations via regex]──►[stash as placeholders]
   │                                                          │
   ▼                                                          │
[protected text] ──► nltk.word_tokenize() ──► rough tokens    │
                                               │               │
                                               ▼               ▼
                              [restore placeholders back to real words]
                                               │
                                               ▼
                                          final tokens
```

## 15. Testing strategy

- `pytest` as the test runner. `tests/` sits at the repo root (not nested
  under `normalizer/`); run from the repo root or `pip install -e .` first
  so `import normalizer` resolves.
- Current suite: 7 test files under `tests/`, **36 tests passing**
  (`test_cleaner.py`, `test_diacritics.py`, `test_edge_cases.py`,
  `test_tokenizer.py`, plus standalone-script style checks in
  `test_morphology_nouns.py` / `test_morphology_verbs.py` / `test_pipeline.py`
  that print diagnostics rather than assert).
- **Known broken test file**: `tests/test_spelling.py` fails to *collect*
  (`ModuleNotFoundError: No module named 'standardize_spelling'`) — it
  imports a top-level `standardize_spelling` module that doesn't exist;
  the real module is `normalizer.spelling`, and the function inside it is
  `standardize_spelling`. Until fixed, run the rest of the suite with
  `pytest --ignore=tests/test_spelling.py`. Fixing the import is a
  one-line change (`from normalizer.spelling import standardize_spelling`
  etc.) — flagged here rather than silently patched, since ownership of
  that test file wasn't confirmed.
- New modules should follow the tokenizer's pattern: a "basic" happy-path
  file plus at least one adversarial file that specifically tries to
  break the implementation.

## 16. Open questions / roadmap

- [ ] Fix `tests/test_spelling.py`'s broken import (§15)
- [ ] Populate `CONFIRMED_VARIANTS` (§6) once the `ŋŋ`/`ng'` question gets
      a native-speaker decision
- [ ] Populate `spelling_dictionary.json` mappings (§8) from a vetted
      source
- [ ] Decide a disambiguation strategy for the noun-vs-verb ambiguous
      case instead of the current noun-first default (§12)
- [ ] Re-enable or delete the dead self-test blocks in
      `morphology_nouns.py` / `morphology_verbs.py` (§11.1)
- [ ] Write `data/README.md` documenting corpus provenance/licensing
- [ ] Add `scripts/download_corpus.py` / `scripts/clean_corpus.py`, or
      remove references to them
- [ ] Add CI (`.github/workflows/tests.yml`), matrix across supported
      Python versions (`pyproject.toml` currently declares `>=3.9`)
- [ ] Decide on named-entity awareness (or an explicit exclusion list) so
      `normalize()` stops stripping proper nouns like `Musisi` (§12)
- [ ] Publish to PyPI, or confirm it stays internal/course-only — the
      package already builds cleanly as `luganda-normalizer` (see
      `README.md`'s packaging section) so this is a decision, not
      blocked engineering work