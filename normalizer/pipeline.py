"""
pipeline.py -- wires every normalization stage together into one
callable, `normalize()`.

STAGE ORDER (and why)
------------------------
 1. clean_text            -- unicode/whitespace/punctuation cleanup
 2. normalize_diacritics  -- canonicalize chars (incl. apostrophe variants)
 3. expand_elisions       -- splits n'X -> na X on now-canonical apostrophes
 4. expand_abbreviations  -- BEFORE lowercasing: acronyms like "URA" are
                             matched case-sensitively, so casing must
                             still be intact here
 5. expand_currency_to_words -- BEFORE generic number expansion: a
                             currency amount ("UGX 50,000") must be
                             recognized and expanded as a unit before
                             plain number expansion tries to touch its
                             digits
 6. expand_datetimes      -- BEFORE generic number expansion, same
                             reasoning: a date/time's digits (16/07/2026,
                             07:00) must be consumed by this stage, not
                             split apart by expand_numbers
 7. expand_numbers        -- whatever plain cardinal numbers remain
                             (phone numbers are protected via
                             edge_cases.PHONE_NUMBER_RE skip-spans, since
                             a phone number is not a count to spell out)
 8. tokenize
 9. lowercase
10. standardize_tokens (spelling dictionary)
11. noun/verb morphology stripping

Each of stages 4-7 is individually toggleable (default on) so a caller
who wants the old, narrower behavior -- or who is feeding in text from
a domain where one of these would be wrong (e.g. a corpus of raw
phone-number logs) -- can turn it off without forking this function.
"""

from normalizer.cleaner import clean_text
from normalizer.contractions import expand_elisions
from normalizer.tokenizer import tokenize
from normalizer.diacritics import normalize_diacritics
from normalizer.spelling import standardize_tokens
from normalizer.morphology_nouns import NounStripper
from normalizer.morphology_verbs import VerbStripper
from normalizer.abbreviations import expand_abbreviations
from normalizer.currency import expand_currency_to_words
from normalizer.datetime import expand_datetimes
from normalizer.numbers import expand_numbers
import normalizer.edge_cases


def normalize(
    text: str,
    *,
    expand_abbrevs: bool = True,
    expand_currency: bool = True,
    expand_dates_times: bool = True,
    expand_nums: bool = True,
) -> str:
    text = clean_text(text)
    text = normalize_diacritics(text)   # canonicalize chars (incl. apostrophe variants) first
    text = expand_elisions(text)        # now safely splits n'X -> na X on canonical apostrophes

    if expand_abbrevs:
        text = expand_abbreviations(text)   # before lowercasing -- acronyms are case-sensitive
    if expand_currency:
        text = expand_currency_to_words(text)   # before number expansion -- consumes amount digits
    if expand_dates_times:
        text = expand_datetimes(text)           # before number expansion -- consumes date/time digits
    if expand_nums:
        phone_spans = [m.span() for m in normalizer.edge_cases.PHONE_NUMBER_RE.finditer(text)]
        text = expand_numbers(text, skip_spans=phone_spans)

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