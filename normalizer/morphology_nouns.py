"""
morphology_nouns.py – Luganda noun-class prefix stripper.
"""

import logging
from typing import Tuple, Optional

# Configure logging (optional – set to WARNING to reduce output)
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class NounStripper:
    """
    Strips noun-class prefixes from Luganda nouns.
    
    Usage:
        stripper = NounStripper()
        root, prefix, class_id = stripper.strip('omuntu')
        # root = 'ntu', prefix = 'omu', class_id = 'MU-BA'
    """

    # ---------- Rules (easy to extend) ----------
    # Each class: singular and plural prefixes
    CLASS_RULES = {
        'MU-BA': {'SG': ['omu', 'mu'], 'PL': ['aba', 'ba']},
        'MU-MI': {'SG': ['omu', 'mu'], 'PL': ['emi', 'mi']},
        'LI-MA': {'SG': ['eri', 'li'], 'PL': ['ama', 'ma']},
        'KI-BI': {'SG': ['eki', 'ki'], 'PL': ['ebi', 'bi']},
        'N':     {'SG': ['en', 'n'],   'PL': ['en', 'n']},
        'LU-N':  {'SG': ['olu', 'lu'], 'PL': ['en', 'n']},
        'KA-BU': {'SG': ['aka', 'ka'], 'PL': ['obu', 'bu']},
        'BU':    {'SG': ['obu', 'bu'], 'PL': []},
    }

    # Words that look like they have a prefix but must NOT be stripped
    FALSE_POSITIVES = {
        'kikumi',   # 100 (not 10)
        'kibuga',   # town (not chief's enclosure)
        'musa',     # proper name
        'muyaga',   # storm
        'mwenge',   # beer
    }

    MIN_ROOT_LENGTH = 2  # safety: reject roots shorter than this

    # ---------- Internals ----------
    def __init__(self):
        """Build a flat prefix map, sorted longest-first."""
        self.prefix_map = []
        for class_id, forms in self.CLASS_RULES.items():
            for prefix in forms.get('SG', []):
                self.prefix_map.append((prefix, class_id, 'SG'))
            for prefix in forms.get('PL', []):
                self.prefix_map.append((prefix, class_id, 'PL'))
        # Sort so 'omu' matches before 'mu'
        self.prefix_map.sort(key=lambda x: len(x[0]), reverse=True)

    # ---------- Main method ----------
    def strip(self, word: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Strip a noun-class prefix if present and safe.

        Returns:
            (root, matched_prefix, class_id)
            If no safe strip, returns (word, None, None).
        """
        # 1. False-positive check
        if word in self.FALSE_POSITIVES:
            LOGGER.warning(f"BLOCKED: '{word}'")
            return word, None, None

        # 2. Try each prefix (longest-first)
        for prefix, class_id, _ in self.prefix_map:
            if word.startswith(prefix):
                root = word[len(prefix):]

                # 3. Safety: root must be long enough
                if len(root) < self.MIN_ROOT_LENGTH:
                    LOGGER.warning(f"SKIP: '{word}' -> root '{root}' too short")
                    continue

                # 4. Safety: root itself must not be a false positive
                if root in self.FALSE_POSITIVES:
                    LOGGER.warning(f"SKIP: '{word}' -> '{root}' is false positive")
                    continue

                LOGGER.info(f"STRIP: '{word}' -> '{root}' ({prefix} : {class_id})")
                return root, prefix, class_id

        # 5. No match
        LOGGER.info(f"NO CHANGE: '{word}'")
        return word, None, None


# ---------- Self-test (runs when executed directly) ----------
if __name__ == "__main__":
    # Minimal test data – you can replace with your full list
    TEST_WORDS = {
        'omuntu':   ('ntu', 'omu', 'MU-BA'),
        'abantu':   ('ntu', 'aba', 'MU-BA'),
        'ekitabo':  ('tabo', 'eki', 'KI-BI'),
        'amazzi':   ('zzi', 'ama', 'LI-MA'),
        'ente':     ('te', 'en', 'N'),
        'oluggi':   ('ggi', 'olu', 'LU-N'),
        'akagaali': ('gaali', 'aka', 'KA-BU'),
        'obulimi':  ('limi', 'obu', 'BU'),
        'kikumi':   ('kikumi', None, None),   # blocked
        'mwa':      ('mwa', None, None),      # too short
    }

    stripper = NounStripper()
    print("\n" + "=" * 50)
    print("SELF-TEST")
    print("=" * 50)

    passed = 0
    for word, (exp_root, exp_prefix, exp_class) in TEST_WORDS.items():
        root, prefix, class_id = stripper.strip(word)
        ok = (root == exp_root and prefix == exp_prefix and class_id == exp_class)
        if ok:
            print(f"✓ PASS {word:15} -> {root:10}")
            passed += 1
        else:
            print(f"✗ FAIL {word:15} -> {root:10}  expected: {exp_root}")

    print("=" * 50)
    print(f"Passed: {passed}/{len(TEST_WORDS)}")
    if passed == len(TEST_WORDS):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    print("=" * 50)