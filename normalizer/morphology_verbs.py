#!/usr/bin/env python3
# sample_verbs.py
# A small set of Luganda sample verbs for testing the verb stripper.
# Format: infinitive -> {root, perfective, meaning, type}

SAMPLE_VERBS = {
    'okukola': {
        'root': 'kola',
        'perfective': 'koze',
        'meaning': 'do, make',
        'type': 'regular',
    },
    'okugenda': {
        'root': 'genda',
        'perfective': 'genze',
        'meaning': 'go',
        'type': 'regular',
    },
    'okusoma': {
        'root': 'soma',
        'perfective': 'somye',
        'meaning': 'read',
        'type': 'regular',
    },
    'okulya': {
        'root': 'lya',
        'perfective': 'lidde',
        'meaning': 'eat',
        'type': 'monosyllabic',
    },
    'okuva': {
        'root': 'va',
        'perfective': 'vudde',
        'meaning': 'come from',
        'type': 'monosyllabic',
    },
    'okusomesa': {
        'root': 'somesa',
        'perfective': 'somesezza',
        'meaning': 'teach (causative)',
        'type': 'causative',
    },
    'okuliisa': {
        'root': 'liisa',
        'perfective': 'liisizza',
        'meaning': 'feed (cause to eat)',
        'type': 'causative',
    },
    'okuliibwa': {
        'root': 'liibwa',
        'perfective': 'liiddwa',
        'meaning': 'be eaten (passive)',
        'type': 'passive',
    },
    'okulabika': {
        'root': 'labika',
        'perfective': 'labise',
        'meaning': 'be visible (stative)',
        'type': 'stative',
    },
    'okukolera': {
        'root': 'kolera',
        'perfective': 'koledde',
        'meaning': 'work for (applicative)',
        'type': 'applicative',
    },
}


def get_root(infinitive: str) -> str:
    return SAMPLE_VERBS.get(infinitive, {}).get('root')

def get_perfective(infinitive: str) -> str:
    return SAMPLE_VERBS.get(infinitive, {}).get('perfective')

def get_meaning(infinitive: str) -> str:
    return SAMPLE_VERBS.get(infinitive, {}).get('meaning')

def get_type(infinitive: str) -> str:
    return SAMPLE_VERBS.get(infinitive, {}).get('type')


if __name__ == "__main__":
    print("Sample verbs loaded:", len(SAMPLE_VERBS))
    for inf, data in SAMPLE_VERBS.items():
        print(f"{inf:15} -> root: {data['root']:8} perfective: {data['perfective']:12} ({data['type']})")