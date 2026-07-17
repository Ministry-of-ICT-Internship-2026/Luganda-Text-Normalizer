
Implements the Bucket A (mechanical) rules identified in the P1 research log
(P1_Research_Log.xlsx) from inspecting real Luganda text sourced from Bukedde
news, Twitter/X, and the Luganda Revised Bible.

This module deliberately does NOT touch anything from Bucket B (diacritic /
spelling variants like the ŋ vs. ng' finding) — those require native-speaker
sign-off and belong in normalize_diacritics(), a separate function built
after that review happens.

Each rule below is traceable back to a specific log entry (see docstring
references to log IDs #1-#7). Number-spacing and emoji handling are now
implemented in edge_cases.py (Sprint 2) and imported here.
"""

import re
import unicodedata

from .edge_cases import fix_number_word_spacing, extract_emoji

# --- Quote / punctuation character maps -------------------------------------

_QUOTE_MAP = {
    "\u201c": '"', "\u201d": '"',   # curly double quotes -> straight  (log #5)
    "\u2018": "'", "\u2019": "'",   # curly single quotes -> straight
}

_DASH_MAP = {
    "\u2013": "-", "\u2014": "-",   # en dash / em dash -> hyphen
}

# Non-printable / control characters to strip outright (keep \n for now,
# it's handled separately by collapse_whitespace).
_CONTROL_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\xa0\u200b\u200c\u200d\ufeff]"
)


def normalize_unicode(text: str) -> str:
    """Normalize to NFC so visually-identical characters are byte-identical.

    Important prerequisite: a large share of "diacritic inconsistency" in
    scraped text is actually an encoding artifact (combining characters vs.
    precomposed characters), not a real spelling variant. Doing this first
    means Bucket B work only has to deal with genuine variants.
    """
    return unicodedata.normalize("NFC", text)


def strip_control_characters(text: str) -> str:
    """Remove non-printable / invisible characters (zero-width spaces, etc.)."""
    return _CONTROL_CHARS_RE.sub(" ", text)


def standardize_quotes_and_dashes(text: str) -> str:
    """Curly quotes -> straight quotes; en/em dash -> hyphen. (log #5)"""
    for variant, canonical in {**_QUOTE_MAP, **_DASH_MAP}.items():
        text = text.replace(variant, canonical)
    return text


def fix_spacing_before_punctuation(text: str) -> str:
    """Remove whitespace immediately before , . ; : ! ?  (log #4)"""
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def collapse_repeated_punctuation(text: str, max_repeat: int = 1) -> str:
    """Collapse runs of !, ?, . to at most `max_repeat` characters. (log #6)

    Default collapses fully (e.g. "!!!!" -> "!") since downstream tokenizers
    generally expect single punctuation marks. If preserving emphasis matters
    for a given task, call with max_repeat=2 or skip this step — this was
    flagged in the log as needing a team decision, not a settled default.
    """
    def _collapse(match):
        ch = match.group(0)[0]
        return ch * max_repeat
    return re.sub(r"([!?.])\1+", _collapse, text)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs to one space, and collapse 3+ newlines
    (irregular mid-sentence breaks, log #2) down to a single paragraph break,
    while still allowing single blank lines to separate paragraphs.
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # A lone newline in the middle of a sentence (not part of a genuine
    # paragraph break) is joined with a space.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)  # re-collapse any new doubles created above
    return text.strip()


def clean_text(text: str, collapse_punctuation: bool = True, strip_emoji: bool = True) -> str:
    """Run the full Bucket A cleaning pipeline in order.

    NOTE: This function intentionally does NOT strip stray non-Luganda
    caption artifacts like the "Portrait" example (log #1). That pattern is
    too easy to confuse with legitimate short English loanwords / code-
    switching (log #7, e.g. "stress", "Chef") to safely automate with a
    generic rule. Handle known scraping artifacts with a source-specific
    pre-filter before calling clean_text(), rather than baking a guess into
    the shared pipeline.

    Mixed-language text (English words embedded in Luganda) is left
    untouched by every step below — see edge_cases.py for the reasoning.
    """
    text = normalize_unicode(text)
    text = strip_control_characters(text)
    text = standardize_quotes_and_dashes(text)
    text = fix_number_word_spacing(text)
    if strip_emoji:
        text, _ = extract_emoji(text)
    text = fix_spacing_before_punctuation(text)
    if collapse_punctuation:
        text = collapse_repeated_punctuation(text)
    text = collapse_whitespace(text)
    return text
"""
Performance check for standardize_spelling.py (Sprint 3 checklist item).
 
This module uses NO regular expressions anywhere -- all matching is plain
string scanning (str indexing/slicing) and dict lookups, both O(n) in the
length of the input. There is therefore no possibility of catastrophic
regex backtracking. This script instead verifies, empirically, that
runtime scales linearly with input size (not quadratically or worse),
and reports throughput on a large synthetic document.
 
Run: python3 check_performance.py
"""
 
import random
import time
 
from standardize_spelling import load_dictionary, standardize_spelling
 
WORD_POOL = [
    "sebo", "nyabo", "webale", "oliotya", "bulunji", "neda", "mpora",
    "cente", "abana", "saawa", "kubanga", "gyebaleko", "twagala",
    "(webale).", '"nedda,', "bulung'i", "unmapped_word", "gyebaleko!",
]
 
 
def make_text(n_words: int) -> str:
    random.seed(42)
    return " ".join(random.choice(WORD_POOL) for _ in range(n_words))
 
 
def time_run(text: str, mappings: dict) -> float:
    start = time.perf_counter()
    standardize_spelling(text, mappings)
    return time.perf_counter() - start
 
 
def main():
    mappings = load_dictionary()
    sizes = [1_000, 10_000, 100_000, 500_000]
    timings = []
 
    print("Linear-scaling check (no regex, so this should scale ~O(n)):\n")
    print(f"{'words':>10} | {'time (s)':>10} | {'ratio vs prev':>14}")
    print("-" * 40)
 
    prev_time = None
    prev_size = None
    for size in sizes:
        text = make_text(size)
        elapsed = time_run(text, mappings)
        timings.append(elapsed)
        ratio_str = "--"
        if prev_time is not None and prev_time > 0:
            size_ratio = size / prev_size
            time_ratio = elapsed / prev_time
            ratio_str = f"{time_ratio:.2f}x (input {size_ratio:.0f}x)"
        print(f"{size:>10} | {elapsed:>10.4f} | {ratio_str:>14}")
        prev_time, prev_size = elapsed, size
 
    # A quadratic (or worse) implementation would show time-ratio >>
    # size-ratio as input grows. Flag if the last step looks non-linear.
    last_size_ratio = sizes[-1] / sizes[-2]
    last_time_ratio = timings[-1] / timings[-2] if timings[-2] > 0 else 0
    print()
    if last_time_ratio > last_size_ratio * 2:
        print("WARNING: runtime growth outpaces input growth -- investigate.")
    else:
        print("OK: runtime growth tracks input growth (linear, as expected).")
 
    words_per_sec = sizes[-1] / timings[-1]
    print(f"\nThroughput on {sizes[-1]:,}-word input: {words_per_sec:,.0f} words/sec")
 
 
if __name__ == "__main__":
    main()
 
