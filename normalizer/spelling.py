"""
Luganda spelling standardizer.

Loads a variant -> canonical mapping table (JSON) and normalizes tokens
before they hit the tokenizer. Words not found in the dictionary are
passed through unchanged -- the function must never crash or mangle
unknown input, since the dictionary is intentionally incomplete.
"""

import json
import os

DEFAULT_DICT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "spelling_dictionary.json"
)


def load_dictionary(path: str = DEFAULT_DICT_PATH) -> dict:
    """Load the mappings dict from the JSON file. Returns {} on any failure
    rather than raising, so a missing/corrupt file degrades to a no-op
    normalizer instead of breaking the whole pipeline."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("mappings", {})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def standardize_spelling(text: str, mappings: dict = None, case_sensitive: bool = False) -> str:
    """
    Replace spelling variants with their canonical form, word by word.

    Args:
        text: raw input string (can be a single word or a full sentence).
        mappings: variant->canonical dict. If None, loads from the default
            dictionary file (loaded once per call unless you pass it in
            yourself -- see standardize_tokens for batch use).
        case_sensitive: if False (default), lookup is case-insensitive but
            the replacement preserves the dictionary's canonical casing.

    Returns:
        The text with known variants replaced. Unknown words are returned
        exactly as given -- this fallback is the critical safety property.
    """
    if mappings is None:
        mappings = load_dictionary()

    if not text:
        return text

    lookup = mappings if case_sensitive else {k.lower(): v for k, v in mappings.items()}

    words = text.split(" ")
    out = []
    for word in words:
        # Strip common trailing punctuation so "webale." still matches "webale"
        stripped = word.strip(".,!?;:\"'()")
        trailing = word[len(stripped):] if stripped else ""
        key = stripped if case_sensitive else stripped.lower()

        if key in lookup:
            out.append(lookup[key] + trailing)
        else:
            # Fallback: unknown word passes through unchanged.
            out.append(word)

    return " ".join(out)


def standardize_tokens(tokens: list, mappings: dict = None) -> list:
    """Same normalization, but for a pre-tokenized list (useful if this runs
    inside a tokenizer pipeline instead of on raw strings)."""
    if mappings is None:
        mappings = load_dictionary()
    lookup = {k.lower(): v for k, v in mappings.items()}
    return [lookup.get(tok.lower(), tok) for tok in tokens]


if __name__ == "__main__":
    # Quick manual smoke test
    sample_sentences = [
        "Sebo, webale nnyo ku bulunji bwo.",
        "Oliotya? Nedda, sirina sente.",
        "This has an unmapped_word_xyz that should pass through untouched.",
    ]

    mappings = load_dictionary()
    print(f"Loaded {len(mappings)} dictionary entries.\n")

    for s in sample_sentences:
        result = standardize_spelling(s, mappings)
        print(f"IN:  {s}")
        print(f"OUT: {result}\n")
