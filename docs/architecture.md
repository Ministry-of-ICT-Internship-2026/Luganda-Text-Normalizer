# Architecture

> Status: skeleton — fill in each section as its module lands.
> Last updated: 2026-07-13

## 1. Overview

`luganda_normalizer` is a Python library for preprocessing Luganda
text for downstream NLP tasks (tokenization now; normalization,
spellchecking, etc. planned). It wraps and extends NLTK rather than
reimplementing a tokenizer from scratch, patching only the specific
places NLTK's English-oriented rules break on Luganda.

## 2. Module status

Reflects the actual files in `luganda_normalizer/` as of the team repo
(7/7/2026). Everything except `__init__.py` and `tokenizer.py` is
currently a stub (0 KB) — owners TBD, fill in as each lands.

| Module               | Status         | File                                      |
|-----------------------|----------------|---------------------------------------------|
| package init          | ✅ done        | `luganda_normalizer/__init__.py`             |
| `tokenizer`            | ✅ done        | `luganda_normalizer/tokenizer.py`            |
| `cleaner`              | 🔲 stub (0 KB) | `luganda_normalizer/cleaner.py`              |
| `diacritics`           | 🔲 stub (0 KB) | `luganda_normalizer/diacritics.py`           |
| `morphology_nouns`     | 🔲 stub (0 KB) | `luganda_normalizer/morphology_nouns.py`     |
| `morphology_verbs`     | 🔲 stub (0 KB) | `luganda_normalizer/morphology_verbs.py`     |
| `spelling`             | 🔲 stub (0 KB) | `luganda_normalizer/spelling.py`             |
| `pipeline`             | 🔲 stub (0 KB) | `luganda_normalizer/pipeline.py`             |
| corpus tooling         | ✅ done        | `scripts/download_corpus.py`, `scripts/clean_corpus.py` |

## 3. `tokenizer` module

### 3.1 Problem it solves

NLTK's `word_tokenize()` uses Penn Treebank rules built for English.
The confirmed (empirically tested, not assumed) failure mode on
Luganda is the **curly apostrophe** (`’`, U+2019) inside elided words
(`ne` + `ekitabo` → `n'ekitabo`) and the `ng'` letter substitute for ŋ.
NLTK splits `b’omu` into three broken tokens (`b`, `’`, `omu`) instead
of treating it as one word.

### 3.2 Approach

Mask-before-tokenize: find Luganda word spans (word-boundary regex
requiring at least one apostrophe group), swap them for alphanumeric
placeholders, run standard `nltk.word_tokenize()` on the rest, restore
the placeholders (substring-based restore, not exact-match — see code
comments for why). Plain words with no apostrophe are left untouched so
NLTK's own abbreviation handling (`Dr.`, etc.) keeps working.

### 3.3 Known limitations (documented, not silently papered over)

- The `ng'`/elision ambiguity (same 3 characters can be a single letter
  *or* the tail of an elided `nga`) isn't resolved — both are treated
  identically (never split), which is the safe default but not always
  linguistically "correct." Real resolution would need a lexicon.
- Malformed double apostrophes (typos/bad OCR, e.g. `n''ekitabo`) are
  not specially handled; would need a cleanup pass upstream of
  tokenization.

### 3.4 Test coverage

Three test files, increasing in difficulty:
- `test_tokenizer.py` — basic elision cases (5)
- `test_tokenizer_hard.py` — quote collisions, numbers, punctuation
  clusters, placeholder-leak regression guard (12)
- `test_tokenizer_deep.py` — diacritics, code-switching, abbreviations,
  multiline input, documented limitations (10)

## 4. `cleaner` module — stub, not yet implemented

Presumed scope from filename (confirm with owner and update this once
code lands): raw-text cleanup prior to tokenization — HTML/markup
stripping, whitespace normalization, encoding fixes. Worth deciding
whether this runs *before* `tokenizer.tokenize()` in the pipeline, or
whether some of this logic already belongs inside `tokenizer.py`
(e.g. the apostrophe-canonicalization it already does).

## 5. `diacritics` module — stub, not yet implemented

Presumed scope: tone-mark (á/à/â) handling. This directly follows up
on a **known limitation already logged in the tokenizer tests**
(`test_tokenizer_deep.py::01_tone_marked_diacritic_vowels`) — the
tokenizer's word regex accepts diacritics as part of a word, but
nothing yet normalizes/strips/analyzes them. Whoever owns this module
should read that test case first.

## 6. `morphology_nouns` module — stub, not yet implemented

Presumed scope: Luganda noun-class prefix analysis (segmenting
class-marker prefixes, e.g. recognizing `omu-`, `aba-`, `eki-` classes).
No design decisions made yet on output format (tagged tuples? a class
enum? flat strings?) — needs a decision before implementation starts,
since `pipeline.py` will need to consume whatever shape this returns.

## 7. `morphology_verbs` module — stub, not yet implemented

Presumed scope: verb morphology — subject/object markers, tense/aspect
affixes, final vowel. Same open question as `morphology_nouns` on
output format; ideally both morphology modules agree on a shared
convention before either is built.

## 8. `spelling` module — stub, not yet implemented

Presumed scope: spellchecking/correction. Depends on having a
reference wordlist/lexicon — worth deciding whether that lexicon is
hand-built, derived from `data/sample_corpus.txt`, or sourced
elsewhere (check licensing per `data/README.md`'s existing caveat
about vetting new sources).

## 9. `pipeline` module — stub, not yet implemented

Presumed scope: chains the other modules into one call (e.g.
`cleaner` → `diacritics` → `tokenizer` → morphology → `spelling`).
Order isn't decided yet — should be settled once at least two of the
upstream modules exist, since the pipeline's job is literally to wire
them together in the right sequence.

## 10. Corpus / data pipeline

See `data/README.md` for full provenance and licensing (SALT dataset,
CC-BY-SA-4.0). Pipeline: `scripts/download_corpus.py` →
`scripts/clean_corpus.py` → `data/sample_corpus.txt`.

## 11. Data flow (tokenizer)

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

Once `pipeline.py` exists, this diagram should be replaced with the
full-pipeline flow (cleaner → diacritics → tokenizer → morphology →
spelling), with this tokenizer diagram kept as a sub-diagram.

## 12. Testing strategy

- `pytest` as the test runner, config in `pyproject.toml`
  (`testpaths = ["luganda_normalizer/tests"]`).
- CI: GitHub Actions (`.github/workflows/tests.yml`), matrix across
  Python 3.10/3.11/3.12, runs on every push/PR to `main`.
- New modules should follow the tokenizer's pattern: a "basic" test
  file plus at least one "hard"/adversarial file that specifically
  tries to break the implementation, not just confirm happy-path cases.

## 13. Open questions / roadmap

- [ ] Assign owners to the 6 stub modules (`cleaner`, `diacritics`,
      `morphology_nouns`, `morphology_verbs`, `spelling`, `pipeline`)
- [ ] Agree on a shared output format between `morphology_nouns` and
      `morphology_verbs` before either is implemented
- [ ] Decide `pipeline.py`'s module ordering once ≥2 upstream modules
      exist
- [ ] `diacritics` owner should start from the tokenizer's already-
      logged tone-mark limitation (section 5 above)
- [ ] Expand corpus beyond SALT (license-check any additional sources
      before adding — see `data/README.md`)
- [ ] Packaging: publish to PyPI or keep as internal/course library?
- [ ] Add `setup.py`/editable install docs for teammates once module
      count grows