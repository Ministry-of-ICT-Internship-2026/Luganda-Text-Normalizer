# Contributing

Thanks for helping build out the Luganda Text Normalizer. This project
is part of the Ministry of ICT Internship 2026, and the aim is a
well-tested, honestly-documented preprocessing library for Luganda NLP
— not a demo. Please read this before opening a PR.

## Setup

```bash
git clone <this repo>
cd Luganda-Text-Normalizer
pip install -e ".[dev]"
pytest tests/ -v
```

All 302+ tests should pass before you start (see
[`docs/architecture.md`](docs/architecture.md) for the current count
and known gaps in test collection).

## Project conventions

These are the patterns every existing module follows. New code should
too, so the codebase stays consistent:

1. **Never crash on unexpected input, and never silently produce
   wrong output.** Every module either (a) returns the input
   unchanged when it doesn't recognize something, or (b) raises a
   specific, documented exception (e.g. `NumberTooLargeError`,
   `DateExpandError`) that callers can catch. Guessing at an
   expansion you're not confident about is worse than leaving the
   text untouched — see point 2.

2. **Do not guess at linguistic facts you can't confirm.** Every
   dictionary (`spelling_dictionary.json`, `abbreviations_dictionary.json`)
   and every module docstring in this project is explicit about what's
   confirmed vs. best-effort. If you're adding a new word, phrase, or
   rule and you're not sure it's correct Luganda, either don't add it,
   or add it with an inline comment flagging it as unconfirmed and
   needing native-speaker review. Wrong output that *looks* confident
   is a worse failure mode than an honest gap.

3. **Document every simplifying assumption in the module docstring**,
   not just in a commit message or PR description. Someone reading
   `numbers.py` six months from now should be able to find, in the
   file itself, exactly why magnitudes ≥ 1,000,000 aren't supported.

4. **Every new module needs its own test file** (`tests/test_<module>.py`),
   covering not just happy-path cases but boundary/error conditions:
   invalid input, empty strings, the documented limitation itself
   (e.g. a test that confirms `NumberTooLargeError` actually raises at
   the boundary). Follow the tokenizer's pattern of a "basic" file plus
   at least one file that specifically tries to break the
   implementation.

5. **Check for interaction effects with existing modules**, especially
   `morphology_nouns.py` / `morphology_verbs.py`. Adding new Luganda
   vocabulary anywhere in the pipeline (e.g. the numeral words in
   `numbers.py`) can look exactly like a noun-class prefix + root to
   the morphology strippers and get wrongly stripped. If you add new
   closed-class vocabulary, add it to `stopwords.CLOSED_CLASS` and
   re-run the full suite — a passing test file for your new module in
   isolation does not guarantee the integrated pipeline is correct.

6. **Keep the "preserve rather than rewrite" stance for ambiguous
   cases**, especially anything involving mixed-language
   (code-switching) text — see `edge_cases.py`'s existing rationale.
   Detection/tagging (like `code_switching.py`) is fine to add;
   silently rewriting or deleting content you're not sure about is not.

## Adding to a dictionary file

`spelling_dictionary.json` and `abbreviations_dictionary.json` both
start from an explicit `_comment` field explaining the vetting policy.
Follow it: only add an entry once you (or a native speaker on the
team) have confirmed it's a real, stable variant/expansion — not by
analogy or guesswork. An empty or small table is a safe no-op; a wrong
entry actively corrupts every text that contains it.

## Updating the docs

If your change adds a module, changes the pipeline order, or resolves
(or discovers) a documented limitation, update
[`docs/architecture.md`](docs/architecture.md) and
[`README.md`](README.md) in the same PR — not as a follow-up. Stale
docs (module descriptions that don't match the code) are worse than no
docs, because they actively mislead the next contributor.

## Running a single test file

```bash
pytest tests/test_numbers.py -v
```

Two files (`tests/test_morphology_nouns.py`,
`tests/test_morphology_verbs.py`) are standalone scripts, not pytest
modules — run them directly with `python tests/test_morphology_nouns.py`.
Converting them to real pytest functions is on the roadmap (see
`docs/architecture.md`) and would be a welcome contribution.

## Pull requests

- Keep PRs scoped to one module or one clearly-related group of
  changes where possible.
- Include the test file(s) for any new code.
- Run `pytest tests/ -q` and paste the pass count in the PR
  description.
- Call out any new documented limitation explicitly in the PR
  description, even if it's also in the code — reviewers should not
  have to hunt for it.
