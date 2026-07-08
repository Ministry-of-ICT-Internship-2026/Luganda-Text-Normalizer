"""
noun_stripper.py

Strips noun‑class prefixes from Luganda nouns.
Uses a prefix map built from class definitions.
Self‑tests against morphology_nouns.py if available.
"""

import logging
from typing import Tuple, Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class NounStripper:
    """
    Strips noun‑class prefixes from Luganda nouns.
    Handles 3 core classes by default – easily extended.
    """

    # ----- 1. Prefix definitions – add more classes here -----
    _CLASS_PREFIXES: Dict[str, Dict[str, List[str]]] = {
        'MU-BA': {'SG': ['omu', 'mu'], 'PL': ['aba', 'ba']},
        'MU-MI': {'SG': ['omu', 'mu'], 'PL': ['emi', 'mi']},
        'KI-BI': {'SG': ['eki', 'ki'], 'PL': ['ebi', 'bi']},
        # Uncomment when ready:
        # 'LI-MA': {'SG': ['eri', 'li'], 'PL': ['ama', 'ma']},
        # 'N':     {'SG': ['en', 'n'],   'PL': ['en', 'n']},
        # 'LU-N':  {'SG': ['olu', 'lu'], 'PL': ['en', 'n']},
        # 'KA-BU': {'SG': ['aka', 'ka'], 'PL': ['obu', 'bu']},
    }

    # ----- 2. False‑positive blocklist (words that must NOT be stripped) -----
    _FALSE_POSITIVES: set[str] = {
        'kikumi',   # 100 – would become "kumi" (10)
        'kibuga',   # town – would become "buga" (chief's enclosure)
        'musa',     # grace / proper name
        'muyaga',   # storm
        'mwenge',   # beer
    }

    # ----- 3. Minimum root length safety threshold -----
    _MIN_ROOT_LENGTH: int = 2

    def __init__(self, enable_logging: bool = True):
        """
        Initialize the noun stripper.

        Args:
            enable_logging: If True, log strip decisions at INFO level.
        """
        self.enable_logging = enable_logging
        # Build a flat prefix map sorted by length descending
        self.prefix_map: List[Tuple[str, str, str]] = []
        for cls, forms in self._CLASS_PREFIXES.items():
            for prefix in forms['SG']:
                self.prefix_map.append((prefix, cls, 'SG'))
            for prefix in forms['PL']:
                self.prefix_map.append((prefix, cls, 'PL'))
        self.prefix_map.sort(key=lambda x: len(x[0]), reverse=True)

    def _log(self, message: str, level: str = 'info') -> None:
        """Internal logging helper."""
        if not self.enable_logging:
            return
        if level == 'warning':
            LOGGER.warning(message)
        else:
            LOGGER.info(message)

    def strip(self, word: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Strip a noun‑class prefix if present and safe.

        Args:
            word: The Luganda noun (e.g., 'omuntu', 'ekitabo').

        Returns:
            Tuple[str, Optional[str], Optional[str]]:
                - stripped root (or original if no safe strip)
                - matched prefix (or None)
                - noun class ID (or None)
        """
        # 1. False‑positive block
        if word in self._FALSE_POSITIVES:
            self._log(f"BLOCKED: '{word}' (false positive)", 'warning')
            return word, None, None

        # 2. Try each prefix (longest first to resolve overlaps like 'omu' vs 'mu')
        for prefix, cls_id, _ in self.prefix_map:
            if word.startswith(prefix):
                root = word[len(prefix):]

                # 3. Safety: root must be at least MIN_ROOT_LENGTH characters
                if len(root) < self._MIN_ROOT_LENGTH:
                    self._log(f"SKIP: '{word}' -> root '{root}' too short", 'warning')
                    continue

                # 4. Safety: stripped root must not itself be a false positive
                if root in self._FALSE_POSITIVES:
                    self._log(f"SKIP: '{word}' -> '{root}' is a false positive", 'warning')
                    continue

                self._log(f"STRIP: '{word}' -> '{root}'  ({prefix} : {cls_id})")
                return root, prefix, cls_id

        # 5. No prefix matched
        self._log(f"NO CHANGE: '{word}'")
        return word, None, None

    def strip_batch(self, words: List[str]) -> List[Dict[str, Any]]:
        """
        Strip prefixes from a batch of words.

        Args:
            words: List of Luganda nouns.

        Returns:
            List of dicts with keys: 'original', 'root', 'prefix', 'class'.
        """
        results = []
        for word in words:
            root, prefix, cls_id = self.strip(word)
            results.append({
                'original': word,
                'root': root,
                'prefix': prefix,
                'class': cls_id,
            })
        return results

    def add_false_positive(self, word: str) -> None:
        """Add a word to the false‑positive blocklist."""
        self._FALSE_POSITIVES.add(word)
        self._log(f"Added to false positives: '{word}'", 'warning')

    def remove_false_positive(self, word: str) -> None:
        """Remove a word from the false‑positive blocklist."""
        if word in self._FALSE_POSITIVES:
            self._FALSE_POSITIVES.remove(word)
            self._log(f"Removed from false positives: '{word}'", 'warning')


# ============================================================================
# Self‑test: runs against morphology_nouns.py if available
# ============================================================================
if __name__ == "__main__":
    # Try to import the sample nouns
    try:
        from morphology_nouns import MORPHOLOGY_NOUNS
        print(f"✓ Loaded {len(MORPHOLOGY_NOUNS)} nouns from morphology_nouns.py")
        test_data = MORPHOLOGY_NOUNS
    except ImportError:
        print("⚠️  morphology_nouns.py not found. Using fallback test set.")
        # Minimal fallback for testing
        test_data = {
            'omuntu':   {'root': 'ntu',   'class': 'MU-BA', 'prefix': 'omu'},
            'abantu':   {'root': 'ntu',   'class': 'MU-BA', 'prefix': 'aba'},
            'ekitabo':  {'root': 'tabo',  'class': 'KI-BI', 'prefix': 'eki'},
            'kikumi':   {'root': 'kikumi','class': None,   'prefix': None},
            'mwa':      {'root': 'mwa',   'class': None,   'prefix': None},
        }

    stripper = NounStripper(enable_logging=False)  # Silence logs during tests

    passed = 0
    failed = 0
    skipped = 0

    print("\n" + "=" * 50)
    print("Running noun stripper tests...")
    print("=" * 50)

    for word, expected in test_data.items():
        root, prefix, cls_id = stripper.strip(word)
        expected_root = expected.get('root', word)
        expected_cls = expected.get('class')

        # Special case: if expected class is None, the word should remain unchanged
        if expected_cls is None:
            if root == word:
                status = "✓ BLOCKED"
                passed += 1
            else:
                status = "❌ FAILED (should be blocked)"
                failed += 1
            print(f"{status:12} {word:15} -> {root:10}")
            continue

        # Normal case: check root and class
        root_ok = (root == expected_root)
        cls_ok = (cls_id == expected_cls)

        if root_ok and cls_ok:
            status = "✓ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            if not root_ok:
                print(f"   Root mismatch: expected '{expected_root}', got '{root}'")
            if not cls_ok:
                print(f"   Class mismatch: expected '{expected_cls}', got '{cls_id}'")

        print(f"{status:12} {word:15} -> {root:10} (class: {cls_id})")

    print("=" * 50)
    print(f"Tests: {passed} passed, {failed} failed, {skipped} skipped")
    if failed == 0:
        print("✅ All tests passed! Noun stripper is ready for use.")
    else:
        print("❌ Some tests failed – please review your data or logic.")
    print("=" * 50)