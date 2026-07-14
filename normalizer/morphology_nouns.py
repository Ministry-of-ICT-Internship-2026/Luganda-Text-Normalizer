"""
morphology_nouns.py – Luganda noun-class prefix stripper.
"""

import logging
from typing import Tuple, Optional

from normalizer.stopwords import CLOSED_CLASS

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
        'kikumi',    # 100
        'kibuga',    # town
        'musa',      # proper name
        'muyaga',    # storm
        'mwenge',    # beer
        'bizineesi', # "business" — loanword, bi- is not a class prefix here
    }

    MIN_ROOT_LENGTH = 2

    def __init__(self):
        self.prefix_map = []
        for class_id, forms in self.CLASS_RULES.items():
            for prefix in forms.get('SG', []):
                self.prefix_map.append((prefix, class_id, 'SG'))
            for prefix in forms.get('PL', []):
                self.prefix_map.append((prefix, class_id, 'PL'))
        self.prefix_map.sort(key=lambda x: len(x[0]), reverse=True)

    def strip(self, word: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Strip a noun-class prefix if present and safe.
        Returns (root, matched_prefix, class_id), or (word, None, None).
        """
        if word in CLOSED_CLASS:
            LOGGER.info(f"CLOSED-CLASS, SKIP: '{word}'")
            return word, None, None

        if word in self.FALSE_POSITIVES:
            LOGGER.warning(f"BLOCKED: '{word}'")
            return word, None, None

        for prefix, class_id, _ in self.prefix_map:
            if word.startswith(prefix):
                root = word[len(prefix):]

                if len(root) < self.MIN_ROOT_LENGTH:
                    LOGGER.warning(f"SKIP: '{word}' -> root '{root}' too short")
                    continue

                if root in self.FALSE_POSITIVES:
                    LOGGER.warning(f"SKIP: '{word}' -> '{root}' is false positive")
                    continue

                LOGGER.info(f"STRIP: '{word}' -> '{root}' ({prefix} : {class_id})")
                return root, prefix, class_id

        LOGGER.info(f"NO CHANGE: '{word}'")
        return word, None, None

"""

# ---------- Self-test (runs when executed directly) ----------
if __name__ == "__main__":
    TEST_WORDS = {
        'omuntu':   ('ntu', 'omu', 'MU-BA'),
        'abantu':   ('ntu', 'aba', 'MU-BA'),
        'ekitabo':  ('tabo', 'eki', 'KI-BI'),
        'amazzi':   ('zzi', 'ama', 'LI-MA'),
        'ente':     ('te', 'en', 'N'),
        'oluggi':   ('ggi', 'olu', 'LU-N'),
        'akagaali': ('gaali', 'aka', 'KA-BU'),
        'obulimi':  ('limi', 'obu', 'BU'),
        'kikumi':   ('kikumi', None, None),
        'mwa':      ('mwa', None, None),
        'abamu':    ('abamu', None, None),
        'nga':      ('nga', None, None),
        'bizineesi':('bizineesi', None, None),
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
    print("✅ All tests passed!" if passed == len(TEST_WORDS) else "❌ Some tests failed.")
    print("=" * 50)

    """