#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
morphology_verbs.py – Luganda verb prefix stripper.
"""

import logging
from typing import Tuple, List

from normalizer.stopwords import CLOSED_CLASS

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class VerbStripper:
    """
    Strips common verb prefixes from Luganda verbs.

    Handles:
        - Infinitive (oku-)
        - Negative prefixes (si-, to-, te-, tetu-, temu-, teba-)
        - Subject markers (n-, o-, a-, tu-, mu-, ba-, and vowel-initial variants)
        - Tense prefixes (naa-, na-, li-, a-)
        - Object infixes (mu-, ba-, ki-, etc.)
    """

    INFINITIVE = 'oku'
    NEGATIVE = ['tetu', 'temu', 'teba', 'te', 'to', 'si']
    # These already bake a subject marker into the negative — don't
    # also strip a subject prefix afterward (that's what caused
    # 'tebalina' -> 'na' instead of 'lina').
    COMPOUND_NEGATIVES = {'tetu', 'temu', 'teba'}

    SUBJECT = ['tw', 'tu', 'mw', 'mu', 'b', 'ba', 'n', 'o', 'a']
    TENSE = ['naa', 'na', 'li', 'a']
    OBJECT = ['mu', 'ba', 'mi', 'bi', 'ki', 'li', 'ma']

    MIN_ROOT_LENGTH = 2

    # Heuristic only, not a real POS tag: most finite Luganda verbs end
    # in -a or -e. Filters out an easy class of non-verbs before we
    # start stripping affixes off them.
    LIKELY_VERB_ENDINGS = ('a', 'e')

    def _looks_like_verb(self, word: str) -> bool:
        if word.startswith(self.INFINITIVE):
            return True
        return word.endswith(self.LIKELY_VERB_ENDINGS)

    def strip(self, word: str) -> Tuple[str, List[str]]:
        """
        Strip prefixes from a verb form.
        Returns (root, list_of_removed_parts). Backs off to the
        original word if the input isn't verb-shaped, is closed-class,
        or stripping would leave a root shorter than MIN_ROOT_LENGTH.
        """
        if word in CLOSED_CLASS:
            LOGGER.info(f"CLOSED-CLASS, SKIP: '{word}'")
            return word, []

        if not self._looks_like_verb(word):
            LOGGER.info(f"NOT VERB-SHAPED, SKIP: '{word}'")
            return word, []

        modified = word
        removed = []
        negative_was_compound = False

        # 1. Infinitive
        if modified.startswith(self.INFINITIVE):
            modified = modified[3:]
            removed.append('infinitive:oku')

        # 2. Negative
        for prefix in self.NEGATIVE:
            if modified.startswith(prefix):
                modified = modified[len(prefix):]
                removed.append(f'negative:{prefix}')
                negative_was_compound = prefix in self.COMPOUND_NEGATIVES
                break

        # 3. Subject — skip if a compound negative already consumed it
        if not negative_was_compound:
            for prefix in self.SUBJECT:
                if modified.startswith(prefix) and len(modified) > len(prefix):
                    modified = modified[len(prefix):]
                    removed.append(f'subject:{prefix}')
                    break

        # 4. Tense — wider safety margin (root must stay >= 3 chars)
        for prefix in self.TENSE:
            if modified.startswith(prefix) and len(modified) > len(prefix) + 2:
                modified = modified[len(prefix):]
                removed.append(f'tense:{prefix}')
                break

        # 5. Object infix — same wider margin
        for prefix in self.OBJECT:
            if modified.startswith(prefix) and len(modified) > len(prefix) + 2:
                modified = modified[len(prefix):]
                removed.append(f'object:{prefix}')
                break

        # Final safety net: never return a fragment that's too short
        if len(modified) < self.MIN_ROOT_LENGTH:
            LOGGER.warning(f"OVER-STRIP, REVERT: '{word}' -> '{modified}' too short")
            return word, []

        if removed:
            LOGGER.info(f"STRIP: '{word}' -> '{modified}' {removed}")
        else:
            LOGGER.info(f"NO CHANGE: '{word}'")

        return modified, removed

"""
# ---------- Self-test ----------
if __name__ == "__main__":
    stripper = VerbStripper()

    test_cases = [
        ('okukola', 'kola'),
        ('nkola', 'kola'),
        ('sikola', 'kola'),
        ('nnaakola', 'kola'),
        ('twakikola', 'kola'),
        ('akolera', 'kolera'),
        ('tebalina', 'lina'),   # negative-only strip, correct root kept
        ('nga', 'nga'),         # closed-class, untouched
        ('abasuubuzi', 'abasuubuzi'),  # not verb-shaped, untouched
    ]

    print("\n" + "=" * 50)
    print("VERB STRIPPER – SELF-TEST")
    print("=" * 50)

    passed = 0
    for word, expected in test_cases:
        root, removed = stripper.strip(word)
        ok = root == expected
        if ok:
            passed += 1
        print(f"{'✅' if ok else '❌'} {word:15} -> {root:10}  {removed}")

    print("=" * 50)
    print(f"Passed: {passed}/{len(test_cases)}")
    print("✅ All tests passed!" if passed == len(test_cases) else "❌ Some tests failed.")
    print("=" * 50)
"""