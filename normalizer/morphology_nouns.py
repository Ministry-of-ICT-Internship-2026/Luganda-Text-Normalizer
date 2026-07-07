# Handles 3 core classes (MU‑BA, MU‑MI, KI‑BI) – easily extended to 5+.

import logging
from typing import Tuple, Optional, Dict, List

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class NounStripper:
    """
    A clean, testable noun‑class prefix stripper.
    """

    # Prefix data – extend this dictionary to add more classes.
    _CLASS_PREFIXES = {
        'MU-BA': {'SG': ['omu', 'mu'], 'PL': ['aba', 'ba']},
        'MU-MI': {'SG': ['omu', 'mu'], 'PL': ['emi', 'mi']},
        'KI-BI': {'SG': ['eki', 'ki'], 'PL': ['ebi', 'bi']},
    }

    # Words that look like they have a prefix but must NOT be stripped.
    _FALSE_POSITIVES = {
        'kikumi',  # 100
        'kibuga',  # town
        'musa',    # grace / proper name
        'muyaga',  # storm
        'mwenge',  # beer
    }

    def __init__(self):
        # Build a flat prefix map and sort by descending length.
        self.prefix_map: List[Tuple[str, str, str]] = []
        for cls, forms in self._CLASS_PREFIXES.items():
            for prefix in forms['SG']:
                self.prefix_map.append((prefix, cls, 'SG'))
            for prefix in forms['PL']:
                self.prefix_map.append((prefix, cls, 'PL'))
        self.prefix_map.sort(key=lambda x: len(x[0]), reverse=True)

    def strip(self, word: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Strip a noun‑class prefix if present and safe.

        Returns:
            (root, matched_prefix, class_id)
            If no safe strip, returns (word, None, None).
        """
        # 1. False‑positive block
        if word in self._FALSE_POSITIVES:
            LOGGER.warning(f"BLOCKED: '{word}' (false positive)")
            return word, None, None

        # 2. Try each prefix (longest first)
        for prefix, cls_id, _ in self.prefix_map:
            if word.startswith(prefix):
                root = word[len(prefix):]

                # 3. Safety: root must be ≥ 2 characters
                if len(root) < 2:
                    LOGGER.warning(f"SKIP: '{word}' -> root '{root}' too short")
                    continue

                # 4. Safety: stripped root must not itself be a false positive
                if root in self._FALSE_POSITIVES:
                    LOGGER.warning(f"SKIP: '{word}' -> '{root}' is a false positive")
                    continue

                LOGGER.info(f"STRIP: '{word}' -> '{root}'  ({prefix} : {cls_id})")
                return root, prefix, cls_id

        LOGGER.info(f"NO CHANGE: '{word}'")
        return word, None, None


# ---------- Quick demo / test ----------
if __name__ == "__main__":
    stripper = NounStripper()
    tests = [
        ('omuntu',   'ntu',    'MU-BA'),
        ('abantu',   'ntu',    'MU-BA'),
        ('ekitabo',  'tabo',   'KI-BI'),
        ('kikumi',   'kikumi', None),   # blocked
        ('mwa',      'mwa',    None),   # short root
    ]

    print("Running tests...")
    for word, expected_root, expected_cls in tests:
        root, pref, cls_id = stripper.strip(word)
        assert root == expected_root, f"Failed: {word} -> {root}, expected {expected_root}"
        assert cls_id == expected_cls, f"Failed: {word} class {cls_id}, expected {expected_cls}"
        print(f"✓ {word:10} -> {root:10} (class: {cls_id})")
    print("All tests passed.")