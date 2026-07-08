"""
verb_stripper.py – Refactored, clean Luganda verb morphology stripper.
Strips: infinitive, subject, negative, tense, object, derivational suffixes,
perfective mapping, and normalises final vowel.
"""

import logging
from typing import Tuple, List, Dict, Optional

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class VerbStripper:
    """Clean, minimal verb morphology stripper."""

    # ---- Constants ----
    INFINITIVE = 'oku'
    SUBJECT = ['tw', 'tu', 'mw', 'mu', 'b', 'ba', 'n', 'o', 'a']
    NEGATIVE = ['tetu', 'temu', 'teba', 'te', 'to', 'si']
    TENSE = ['naa', 'na', 'li', 'a']
    OBJECT = ['mu', 'ba', 'mi', 'bi', 'ki', 'li', 'ma']
    DERIV = ['ibw', 'ir', 'er', 'an', 'ik', 'y']
    MIN_ROOT = 2

    def __init__(self, enable_perfective: bool = True, log: bool = True):
        """
        enable_perfective: if True, map perfective stems to base roots.
        log: if True, log stripping decisions.
        """
        self.enable_perfective = enable_perfective
        self.log = log
        # Load perfective mapping from morphology_verbs.py if available
        self.perfective_map = self._load_perfective_map()

    def _load_perfective_map(self) -> Dict[str, str]:
        """Load perfective->base mapping from morphology_verbs.py or fallback."""
        try:
            from morphology_verbs import MORPHOLOGY_VERBS
            mapping = {}
            for inf, data in MORPHOLOGY_VERBS.items():
                if data.get('perfective') and data.get('root'):
                    mapping[data['perfective']] = data['root']
            self._log(f"Loaded {len(mapping)} perfective mappings from morphology_verbs.py")
            return mapping
        except ImportError:
            self._log("morphology_verbs.py not found; using fallback map", 'warning')
            # Minimal fallback mapping
            return {
                'koze': 'kola', 'genze': 'genda', 'somye': 'soma',
                'labye': 'laba', 'guze': 'gula', 'badde': 'beera',
                'lidde': 'lya', 'vudde': 'va', 'nywedde': 'nywa',
                'zze': 'dda', 'somesezza': 'somesa', 'liisizza': 'liisa',
                'liiddwa': 'liibwa', 'labise': 'labika', 'somerde': 'somera',
            }

    def _log(self, msg: str, level: str = 'info') -> None:
        if self.log:
            getattr(LOGGER, level)(msg)

    def _strip_prefix(self, text: str, prefixes: List[str], marker: str, removed: List[str]) -> Tuple[str, bool]:
        """Strip a prefix from text if it matches a prefix in the list."""
        for prefix in prefixes:
            if text.startswith(prefix) and len(text) > len(prefix):
                new_text = text[len(prefix):]
                removed.append(f'{marker}:{prefix}')
                self._log(f"{marker.upper()}: {new_text}")
                return new_text, True
        return text, False

    def _strip_tense(self, text: str, removed: List[str]) -> str:
        """Strip tense markers (requires extra validation)."""
        for tense in self.TENSE:
            if text.startswith(tense) and len(text) > len(tense) + 1:
                new_text = text[len(tense):]
                removed.append(f'tense:{tense}')
                self._log(f"TENSE: {new_text}")
                return new_text
        return text

    def _strip_object(self, text: str, removed: List[str]) -> str:
        """Strip object infixes (requires extra validation)."""
        for obj in self.OBJECT:
            if text.startswith(obj) and len(text) > len(obj) + 1:
                new_text = text[len(obj):]
                removed.append(f'object:{obj}')
                self._log(f"OBJECT: {new_text}")
                return new_text
        return text

    def _strip_derivational(self, stem: str, removed: List[str]) -> str:
        """Strip derivational suffixes from the end."""
        changed = True
        while changed and len(stem) >= self.MIN_ROOT:
            changed = False
            if stem[-1] not in 'aeiou':
                break
            core = stem[:-1]
            for suff in self.DERIV:
                if core.endswith(suff):
                    new_stem = core[:-len(suff)] + stem[-1]
                    if len(new_stem) >= self.MIN_ROOT:
                        stem = new_stem
                        removed.append(f'deriv:{suff}')
                        self._log(f"DERIV: {stem}")
                        changed = True
                        break
        return stem

    def _normalise_final_vowel(self, text: str) -> str:
        """Normalise final vowel to 'a'."""
        if text and text[-1] in 'eiou' and len(text) > 1:
            text = text[:-1] + 'a'
            self._log(f"NORMALISE: {text}")
        return text

    def _strip_marker(self, text: str, markers: List[str], name: str, 
                      removed: List[str], min_len: int = 1) -> str:
        """Strip a marker from text (infinitive, negative, subject, etc)."""
        for marker in markers:
            if text.startswith(marker) and len(text) > len(marker) + min_len - 1:
                new_text = text[len(marker):]
                removed.append(f'{name}:{marker}')
                self._log(f"{name.upper()}: {new_text}")
                return new_text
        return text

    def strip(self, word: str) -> Tuple[str, List[str]]:
        """
        Strip all verb morphology from a Luganda verb form.
        Returns (canonical_root, list_of_removed_parts).
        """
        modified = word
        removed = []

        # 1. Perfective mapping (if enabled)
        if self.enable_perfective and modified in self.perfective_map:
            root = self.perfective_map[modified]
            removed.append(f'perfective:{modified}')
            self._log(f"PERFECTIVE: {modified} -> {root}")
            return root, removed

        # 2. Infinitive
        if modified.startswith(self.INFINITIVE):
            modified = modified[3:]
            removed.append('infinitive:oku')
            self._log(f"INFINITIVE: {modified}")

        # 3-6. Strip markers using helper
        modified = self._strip_marker(modified, self.NEGATIVE, 'negative', removed)
        modified = self._strip_marker(modified, self.SUBJECT, 'subject', removed)
        modified = self._strip_marker(modified, self.TENSE, 'tense', removed, 2)
        modified = self._strip_marker(modified, self.OBJECT, 'object', removed, 2)

        # 7. Derivational suffixes (peel from end)
        modified = self._strip_derivational(modified, removed)

        # 8. Normalise final vowel to 'a'
        modified = self._normalise_final_vowel(modified)

        if not removed:
            self._log(f"NO CHANGE: {word}")

        return modified, removed


# ===== Minimal self-test =====
if __name__ == "__main__":
    s = VerbStripper(log=False)
    tests = [
        ('okukola', 'kola'),
        ('nkola', 'kola'),
        ('tebakola', 'kola'),
        ('nnaakola', 'kola'),
        ('koze', 'kola'),
        ('lidde', 'lya'),
        ('okusomesa', 'somesa'),
        ('okuliibwa', 'liibwa'),
        ('okulabika', 'labika'),
    ]
    print("Running verb stripper tests...")
    for word, expected in tests:
        root, parts = s.strip(word)
        ok = root == expected
        status = '✓' if ok else '✗'
        print(f"{status} {word:15} -> {root:10}  {parts}")
    print("Done.")