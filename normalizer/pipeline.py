from normalizer.cleaner import clean_text
from normalizer.tokenizer import tokenize
from normalizer.diacritics import normalize_diacritics
from normalizer.spelling import correct_spelling
from normalizer.morphology_nouns import analyze_nouns
from normalizer.morphology_verbs import analyze_verbs

def normalize(text: str) -> str:
    text = clean_text(text)
    text = normalize_diacritics(text)
    tokens = tokenize(text)
    tokens = [correct_spelling(t) for t in tokens]
    tokens = analyze_nouns(tokens)
    tokens = analyze_verbs(tokens)
    return " ".join(tokens)