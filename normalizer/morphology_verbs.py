#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
morphology_verbs.py – Luganda verb prefix stripper.
"""

from typing import Tuple, List


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

    # ---------- Configuration ----------
    INFINITIVE = 'oku'

    NEGATIVE = ['tetu', 'temu', 'teba', 'te', 'to', 'si']

    SUBJECT = ['tw', 'tu', 'mw', 'mu', 'b', 'ba', 'n', 'o', 'a']

    TENSE = ['naa', 'na', 'li', 'a']

    OBJECT = ['mu', 'ba', 'mi', 'bi', 'ki', 'li', 'ma']

    def strip(self, word: str) -> Tuple[str, List[str]]:
        """
        Strip prefixes from a verb form.

        Args:
            word: The verb form (e.g., 'nkola', 'okukola')

        Returns:
            Tuple[str, List[str]]: (root, list_of_removed_parts)

        Example:
            >>> stripper = VerbStripper()
            >>> stripper.strip('nkola')
            ('kola', ['subject:n'])
        """
        modified = word
        removed = []

        # 1. Infinitive
        if modified.startswith(self.INFINITIVE):
            modified = modified[3:]
            removed.append('infinitive:oku')

        # 2. Negative
        for prefix in self.NEGATIVE:
            if modified.startswith(prefix):
                modified = modified[len(prefix):]
                removed.append(f'negative:{prefix}')
                break

        # 3. Subject
        for prefix in self.SUBJECT:
            if modified.startswith(prefix) and len(modified) > len(prefix):
                modified = modified[len(prefix):]
                removed.append(f'subject:{prefix}')
                break

        # 4. Tense
        for prefix in self.TENSE:
            if modified.startswith(prefix) and len(modified) > len(prefix) + 1:
                modified = modified[len(prefix):]
                removed.append(f'tense:{prefix}')
                break

        # 5. Object infix
        for prefix in self.OBJECT:
            if modified.startswith(prefix) and len(modified) > len(prefix) + 1:
                modified = modified[len(prefix):]
                removed.append(f'object:{prefix}')
                break

        return modified, removed


# ---------- Self-test ----------
if __name__ == "__main__":
    stripper = VerbStripper()

    test_cases = [
        ('okukola', 'kola'),
        ('nkola', 'kola'),
        ('sikola', 'kola'),
        ('nnaakola', 'kola'),
        ('nkyagala', 'agala'),
        ('twakikola', 'kola'),
        ('okuliibwa', 'liibwa'),
        ('akolera', 'kolera'),
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
        else:
            print(f"❌ FAIL: {word} -> {root} (expected {expected})")
        print(f"{'✅' if ok else '❌'} {word:15} -> {root:10}  {removed}")

    print("=" * 50)
    print(f"Passed: {passed}/{len(test_cases)}")
    if passed == len(test_cases):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    print("=" * 50)