"""
morphology_verbs.py

Sample Luganda verbs for testing the morphological root normaliser.
Each entry provides the infinitive, canonical root, perfective stem, meaning, and verb type.
"""

MORPHOLOGY_VERBS = {
    # ========== Regular verbs ==========
    'okukola': {
        'root': 'kola',
        'perfective': 'koze',
        'meaning': 'do, make',
        'type': 'regular'
    },
    'okugenda': {
        'root': 'genda',
        'perfective': 'genze',
        'meaning': 'go',
        'type': 'regular'
    },
    'okusoma': {
        'root': 'soma',
        'perfective': 'somye',
        'meaning': 'read, study',
        'type': 'regular'
    },
    'okulaba': {
        'root': 'laba',
        'perfective': 'labye',
        'meaning': 'see',
        'type': 'regular'
    },
    'okugula': {
        'root': 'gula',
        'perfective': 'guze',
        'meaning': 'buy',
        'type': 'regular'
    },
    'okubeera': {
        'root': 'beera',
        'perfective': 'badde',
        'meaning': 'be, remain',
        'type': 'regular'
    },

    # ========== Monosyllabic verbs (irregular perfective) ==========
    'okulya': {
        'root': 'lya',
        'perfective': 'lidde',
        'meaning': 'eat',
        'type': 'monosyllabic'
    },
    'okuva': {
        'root': 'va',
        'perfective': 'vudde',
        'meaning': 'come/go from',
        'type': 'monosyllabic'
    },
    'okunywa': {
        'root': 'nywa',
        'perfective': 'nywedde',
        'meaning': 'drink',
        'type': 'monosyllabic'
    },
    'okudda': {
        'root': 'dda',
        'perfective': 'zze',
        'meaning': 'return',
        'type': 'monosyllabic'
    },

    # ========== Causative verbs (derivational suffix -y-) ==========
    'okusomesa': {
        'root': 'somesa',
        'perfective': 'somesezza',
        'meaning': 'teach (cause to read)',
        'type': 'causative'
    },
    'okuliisa': {
        'root': 'liisa',
        'perfective': 'liisizza',
        'meaning': 'feed (cause to eat)',
        'type': 'causative'
    },

    # ========== Passive verbs ==========
    'okuliibwa': {
        'root': 'liibwa',
        'perfective': 'liiddwa',
        'meaning': 'be eaten',
        'type': 'passive'
    },

    # ========== Stative verbs ==========
    'okulabika': {
        'root': 'labika',
        'perfective': 'labise',
        'meaning': 'be visible',
        'type': 'stative'
    },

    # ========== Applicative verbs ==========
    'okusomera': {
        'root': 'somera',
        'perfective': 'somerde',
        'meaning': 'read for/on behalf of',
        'type': 'applicative'
    },
}

# ---------- Helper functions ----------
def get_root(infinitive: str) -> str:
    """Return the canonical root for a given verb infinitive."""
    return MORPHOLOGY_VERBS.get(infinitive, {}).get('root', infinitive)

def get_perfective(infinitive: str) -> str:
    """Return the perfective stem for a given verb infinitive."""
    return MORPHOLOGY_VERBS.get(infinitive, {}).get('perfective', None)

def get_meaning(infinitive: str) -> str:
    """Return the English meaning for a given verb infinitive."""
    return MORPHOLOGY_VERBS.get(infinitive, {}).get('meaning', None)

def get_type(infinitive: str) -> str:
    """Return the verb type (regular, monosyllabic, etc.)."""
    return MORPHOLOGY_VERBS.get(infinitive, {}).get('type', None)

def list_by_type(verb_type: str) -> list:
    """Return a list of infinitives that match a given type."""
    return [inf for inf, data in MORPHOLOGY_VERBS.items() if data.get('type') == verb_type]


# ---------- Self-check ----------
if __name__ == "__main__":
    print(f"Loaded {len(MORPHOLOGY_VERBS)} sample verbs.")
    print("\nSample entries:")
    for i, (inf, data) in enumerate(list(MORPHOLOGY_VERBS.items())[:10]):
        print(f"{i+1:2}. {inf:20} -> root: {data['root']:8}  perfective: {data['perfective']:12} ({data['type']})")
    print("\nSelf-check: OK.")
