"""
contractions.py – expands Luganda apostrophe-elisions before tokenization.

Luganda often drops a vowel and glues a short word onto the next one
with an apostrophe, e.g. 'n'emikyungwa' = 'na' + 'emikyungwa' ("and
jackfruit"). If left alone, the noun/verb strippers mistake the glued
letter for a class prefix and mangle both halves.

Only expand elisions we've explicitly confirmed — same safety
philosophy as FALSE_POSITIVES / CLOSED_CLASS elsewhere in this
project. Add more here as you confirm them; do not guess new ones in,
since an unconfirmed elision will silently corrupt text that wasn't
actually contracted.
"""

import re

# confirmed elision -> full word it stands for
ELISIONS = {
    'n': 'na',   # n'emikyungwa -> na emikyungwa ("and jackfruit")
}

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in ELISIONS) + r")'(?=\w)",
    re.IGNORECASE,
)


def expand_elisions(text: str) -> str:
    """
    Split known apostrophe-contractions into two separate words.

    Example:
        "n'emikyungwa" -> "na emikyungwa"
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1).lower()
        return ELISIONS[key] + " "

    return _PATTERN.sub(_replace, text)


# ---------- Self-test ----------
if __name__ == "__main__":
    test_cases = [
        ("n'emikyungwa", "na emikyungwa"),
        ("Yagula emiyembe n'emikyungwa.", "Yagula emiyembe na emikyungwa."),
        ("emikyungwa", "emikyungwa"),  # no apostrophe -> untouched
    ]

    print("=" * 50)
    print("CONTRACTIONS – SELF-TEST")
    print("=" * 50)
    passed = 0
    for word, expected in test_cases:
        result = expand_elisions(word)
        ok = result == expected
        passed += ok
        print(f"{'✅' if ok else '❌'} {word!r:30} -> {result!r}")
    print(f"Passed: {passed}/{len(test_cases)}")