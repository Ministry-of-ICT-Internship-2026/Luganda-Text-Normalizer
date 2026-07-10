#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
morphology_verbs.py – Simple verb prefix stripper (function-based).
"""

from typing import Tuple, List

# ----- Prefix lists (longer first to avoid conflicts) -----
INFINITIVE = 'oku'

NEGATIVE = ['tetu', 'temu', 'teba', 'te', 'to', 'si']

SUBJECT = ['tw', 'tu', 'mw', 'mu', 'b', 'ba', 'n', 'o', 'a']

TENSE = ['naa', 'na', 'li', 'a']

OBJECT = ['mu', 'ba', 'mi', 'bi', 'ki', 'li', 'ma']


def strip_verb(word: str) -> Tuple[str, List[str]]:
    """
    Strip verb prefixes.
    Returns: (root, list_of_removed_parts)
    """
    mod = word
    removed = []

    # 1. Infinitive
    if mod.startswith(INFINITIVE):
        mod = mod[3:]
        removed.append('infinitive:oku')

    # 2. Negative
    for p in NEGATIVE:
        if mod.startswith(p):
            mod = mod[len(p):]
            removed.append(f'negative:{p}')
            break

    # 3. Subject
    for p in SUBJECT:
        if mod.startswith(p) and len(mod) > len(p):
            mod = mod[len(p):]
            removed.append(f'subject:{p}')
            break

    # 4. Tense
    for p in TENSE:
        if mod.startswith(p) and len(mod) > len(p) + 1:
            mod = mod[len(p):]
            removed.append(f'tense:{p}')
            break

    # 5. Object
    for p in OBJECT:
        if mod.startswith(p) and len(mod) > len(p) + 1:
            mod = mod[len(p):]
            removed.append(f'object:{p}')
            break

    return mod, removed


# ----- Self-test -----
if __name__ == "__main__":
    tests = [
        ('okukola', 'kola'),
        ('nkola', 'kola'),
        ('sikola', 'kola'),
        ('nnaakola', 'kola'),
        ('nkyagala', 'agala'),
        ('twakikola', 'kola'),
    ]

    print("\n" + "=" * 40)
    print("VERB STRIPPER (FUNCTION) – TEST")
    print("=" * 40)

    for word, expected in tests:
        root, removed = strip_verb(word)
        ok = "✅" if root == expected else "❌"
        print(f"{ok} {word:12} -> {root:8}  {removed}")

    print("=" * 40)