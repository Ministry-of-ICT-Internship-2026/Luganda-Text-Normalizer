"""
morphology_nouns.py

Sample Luganda nouns for testing the morphological root normaliser.
Each entry provides the full word, its noun class, prefix, root, and meaning.
"""

MORPHOLOGY_NOUNS = {
    # ========== Class 1/2: MU-BA (people) ==========
    'omuntu': {
        'class': 'MU-BA',
        'prefix': 'omu',
        'root': 'ntu',
        'meaning': 'person'
    },
    'abantu': {
        'class': 'MU-BA',
        'prefix': 'aba',
        'root': 'ntu',
        'meaning': 'people'
    },
    'omusomesa': {
        'class': 'MU-BA',
        'prefix': 'omu',
        'root': 'somesa',
        'meaning': 'teacher'
    },
    'omwana': {
        'class': 'MU-BA',
        'prefix': 'omu',
        'root': 'wana',
        'meaning': 'child'
    },

    # ========== Class 3/4: MU-MI (trees/plants) ==========
    'omuti': {
        'class': 'MU-MI',
        'prefix': 'omu',
        'root': 'ti',
        'meaning': 'tree'
    },
    'emiti': {
        'class': 'MU-MI',
        'prefix': 'emi',
        'root': 'ti',
        'meaning': 'trees'
    },
    'omugaati': {
        'class': 'MU-MI',
        'prefix': 'omu',
        'root': 'gaati',
        'meaning': 'bread (loaf)'
    },

    # ========== Class 7/8: KI-BI (artifacts) ==========
    'ekitabo': {
        'class': 'KI-BI',
        'prefix': 'eki',
        'root': 'tabo',
        'meaning': 'book'
    },
    'ebitabo': {
        'class': 'KI-BI',
        'prefix': 'ebi',
        'root': 'tabo',
        'meaning': 'books'
    },
    'ekibuga': {
        'class': 'KI-BI',
        'prefix': 'eki',
        'root': 'buga',
        'meaning': 'town, city'
    },
    'ekisenge': {
        'class': 'KI-BI',
        'prefix': 'eki',
        'root': 'senge',
        'meaning': 'room'
    },

    # ========== Class 5/6: LI-MA (liquids, abstract) – for extension ==========
    'erinnya': {
        'class': 'LI-MA',
        'prefix': 'eri',
        'root': 'nnya',
        'meaning': 'name'
    },
    'amazzi': {
        'class': 'LI-MA',
        'prefix': 'ama',
        'root': 'zzi',
        'meaning': 'water'
    },

    # ========== Class 9/10: N (animals, borrowed words) – for extension ==========
    'ente': {
        'class': 'N',
        'prefix': 'en',
        'root': 'te',
        'meaning': 'cow'
    },
    'enkoko': {
        'class': 'N',
        'prefix': 'en',
        'root': 'koko',
        'meaning': 'chicken'
    },

    # ========== Class 11/10: LU-N (long/flexible objects) – for extension ==========
    'oluggi': {
        'class': 'LU-N',
        'prefix': 'olu',
        'root': 'ggi',
        'meaning': 'door'
    },

    # ========== Class 12/14: KA-BU (diminutives/collectives) – for extension ==========
    'akagaali': {
        'class': 'KA-BU',
        'prefix': 'aka',
        'root': 'gaali',
        'meaning': 'bicycle'
    },

    # ========== FALSE POSITIVES (words that look like they have a prefix but must NOT be stripped) ==========
    'kikumi': {
        'class': None,
        'prefix': None,
        'root': 'kikumi',
        'meaning': '100 (should not become "kumi" = 10)'
    },
    'kibuga': {
        'class': None,
        'prefix': None,
        'root': 'kibuga',
        'meaning': 'town (should not become "buga" = chief\'s enclosure)'
    },
    'musa': {
        'class': None,
        'prefix': None,
        'root': 'musa',
        'meaning': 'grace / proper name'
    },
    'mwenge': {
        'class': None,
        'prefix': None,
        'root': 'mwenge',
        'meaning': 'beer (should not be stripped)'
    },
}

# ---------- Helper functions ----------
def get_root(word: str) -> str:
    """Return the canonical root for a given noun."""
    return MORPHOLOGY_NOUNS.get(word, {}).get('root', word)

def get_class(word: str) -> str:
    """Return the noun class for a given noun."""
    return MORPHOLOGY_NOUNS.get(word, {}).get('class', None)

def get_prefix(word: str) -> str:
    """Return the expected prefix for a given noun."""
    return MORPHOLOGY_NOUNS.get(word, {}).get('prefix', None)

def get_meaning(word: str) -> str:
    """Return the English meaning for a given noun."""
    return MORPHOLOGY_NOUNS.get(word, {}).get('meaning', None)

# ---------- Self-check ----------
if __name__ == "__main__":
    print(f"Loaded {len(MORPHOLOGY_NOUNS)} sample nouns.")
    print("\nSample entries:")
    for i, (word, data) in enumerate(list(MORPHOLOGY_NOUNS.items())[:10]):
        cls = data.get('class') or 'FALSE-POS'
        print(f"{i+1:2}. {word:15} -> {data['root']:8}  ({cls})  {data['meaning']}")
    print("\nSelf-check: OK.")