# luganda-normalizer

Text preprocessing for Luganda, built for NLP pipelines.

`normalizer` cleans, tokenizes, and normalizes Luganda text so it's ready
for search, embeddings, spellchecking, or any downstream model that needs
consistent input. It wraps NLTK for tokenization and patches the specific
places its English-oriented rules break on Luganda — rather than
reimplementing a tokenizer from scratch.

```python
>>> import normalizer as n
>>> n.normalize("Abaana b'omu kibuga bazannya n'essanyu.")
"ana b'omu buga zannya na essanyu ."
```

> **Import name vs. package name.** You `pip install luganda-normalizer`
> but `import normalizer`. This is intentional — the same pattern as
> `beautifulsoup4` → `import bs4`.

---

## How it works

Text passes through a fixed sequence of stages, each of which is also
usable on its own:

1. **Cleaning** — Unicode normalization, control-character stripping,
   curly-quote/dash canonicalization, punctuation spacing, whitespace
   collapsing. Also handles informal/social text: number vs. abbreviation
   spacing (`4G` stays glued together, `58baliraanwa` gets split apart),
   phone number and currency detection, emoji extraction, hashtag/mention
   surfacing.

2. **Diacritic canonicalization** — merges confirmed spelling variants of
   the same word into one canonical form.

3. **Elision expansion** — Luganda often drops a vowel and glues a short
   word onto the next one with an apostrophe. `n'emikyungwa` becomes
   `na emikyungwa` ("and jackfruit"), case-preserved.

4. **Tokenization** — splits text into words, correctly keeping
   apostrophe-words intact (`n'ekitabo`, `b'omu`) even when the apostrophe
   is the curly `’` character that phones and Word autocorrect to by
   default, and without breaking known abbreviations like `Dr.` in the
   process.

5. **Spelling standardization** — looks up each token against a
   variant → canonical dictionary. Anything not found is passed through
   unchanged.

6. **Morphology stripping** — removes noun-class prefixes (e.g. `omu-`,
   `aba-`, `eki-`) and verb affixes (infinitive, negative, subject,
   tense, object markers), reducing words to their root form.

`normalize()` runs all six stages in order and returns one normalized
string — this is the one-call entry point most callers want. Every stage
is also exported on its own, so you can use just the tokenizer, just the
cleaner, or assemble a custom pipeline instead.

```python
from normalizer import clean_text, tokenize

tokenize("n'ekitabo ky'omusomesa")
# ["n'ekitabo", "ky'omusomesa"]

clean_text("Nkola   bulungi!!!")
# "Nkola bulungi!"
```

## Installation

```bash
pip install luganda-normalizer
```

Or from source, editable (useful while developing):

```bash
git clone <repository-url>
cd Luganda-Text-Normalizer
pip install -e .
```

Requires **Python ≥ 3.9**. The only runtime dependency is `nltk`, which
this library uses to auto-download the tokenizer data it needs the first
time it runs — no manual setup required.

```python
import normalizer      # always this — never "luganda_normalizer"
```

## Quickstart

```python
import normalizer as n

# Full pipeline
n.normalize("Abaana b'omu kibuga bazannya n'essanyu.")

# Tokenize only
n.tokenize("n'ekitabo ky'omusomesa")

# Strip a noun-class prefix
n.NounStripper().strip("omuntu")
# ("ntu", "omu", "MU-BA")

# Strip verb affixes
n.VerbStripper().strip("twakikola")
# ("kola", ["subject:tw", "object:ki"])
```

## License

MIT — see `LICENSE`.