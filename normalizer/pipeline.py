from normalizer.cleaner import clean_text
from normalizer.contractions import expand_elisions
from normalizer.tokenizer import tokenize
from normalizer.diacritics import normalize_diacritics
from normalizer.spelling import standardize_tokens
from normalizer.morphology_nouns import NounStripper
from normalizer.morphology_verbs import VerbStripper


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