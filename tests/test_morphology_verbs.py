#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_morphology_verbs.py – Tests for Luganda verb stripper.
"""

import os
import sys
import importlib.util
from typing import List, Tuple

# ---------- Step 1: Get absolute paths ----------
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
project_root = os.path.dirname(current_dir)
normalizer_dir = os.path.join(project_root, 'normalizer')
module_path = os.path.join(normalizer_dir, 'morphology_verbs.py')

print(f"Project root: {project_root}")
print(f"Module path: {module_path}")

# ---------- Step 2: Import using importlib ----------
if not os.path.exists(module_path):
    print(f"❌ File not found: {module_path}")
    sys.exit(1)

# Load the module from the exact path
spec = importlib.util.spec_from_file_location("morphology_verbs", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Get the VerbStripper class from the loaded module
try:
    VerbStripper = module.VerbStripper
    print("✅ Imported VerbStripper from exact path")
except AttributeError:
    print("❌ VerbStripper class not found in the module")
    sys.exit(1)


# ---------- Step 3: Load test data ----------
DATA_PATH = os.path.join(project_root, 'data', 'verbs.txt')


def load_data(path: str) -> List[Tuple[str, str]]:
    """Load verb test data from tab-separated file."""
    data = []
    if not os.path.exists(path):
        print(f"⚠️  Data file not found: {path}")
        print("   Using fallback minimal dataset.")
        return [
            ('okukola', 'kola'),
            ('nkola', 'kola'),
            ('sikola', 'kola'),
            ('nnaakola', 'kola'),
            ('nkyagala', 'agala'),
            ('twakikola', 'kola'),
        ]

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                data.append((parts[0], parts[1]))

    return data


# ---------- Step 4: Run tests ----------
def run_tests():
    print("\n" + "=" * 60)
    print("TEST: Luganda Verb Stripper")
    print("=" * 60)

    tests = load_data(DATA_PATH)
    stripper = VerbStripper()

    print(f"Loaded {len(tests)} test cases\n")

    passed = 0
    failed = 0
    failures = []

    for word, expected in tests:
        root, _ = stripper.strip(word)
        if root == expected:
            passed += 1
        else:
            failed += 1
            failures.append((word, expected, root))

    # Show progress for small datasets
    if len(tests) <= 50:
        for word, expected in tests:
            root, _ = stripper.strip(word)
            ok = "✅" if root == expected else "❌"
            print(f"{ok} {word:20} -> {root:10}")

    # Show failures
    if failures:
        print("\n--- Failures ---")
        for word, expected, got in failures[:20]:
            print(f"  ❌ {word}: expected '{expected}', got '{got}'")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")

    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()