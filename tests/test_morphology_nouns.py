#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_morphology_noun.py – Unit tests for Luganda noun-class prefix stripper.

This file resides in the 'tests/' folder. It imports the NounStripper
from the sibling folder 'normalizer/' and loads test data from
'../data/nouns.txt'.
"""

import os
import sys
from typing import Dict, Tuple

# ---------- Step 1: Find the project root ----------
# This file is in 'tests/' – the project root is one level up.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # one level up from tests/

# ---------- Step 2: Add the 'normalizer' folder to sys.path ----------
normalizer_dir = os.path.join(project_root, 'normalizer')
if not os.path.exists(normalizer_dir):
    print(f" Folder 'normalizer' not found at {normalizer_dir}")
    sys.exit(1)
sys.path.insert(0, normalizer_dir)   # Now Python can see files inside normalizer/

# ---------- Step 3: Import the NounStripper ----------
try:
    from morphology_nouns import NounStripper
    print(" Imported from morphology_nouns")
except ImportError as e:
    print(f" Could not import NounStripper. Error: {e}")
    print(f"   Looking for: {os.path.join(normalizer_dir, 'morphology_nouns.py')}")
    sys.exit(1)

# ---------- Step 4: Set data file location ----------
DATA_PATH = os.path.join(project_root, 'data', 'nouns.txt')

# ---------- Step 5: Fallback dataset (if data file is missing) ----------
FALLBACK_DATA: Dict[str, Tuple[str, str, str]] = {
    'omuntu': ('ntu', 'omu', 'MU-BA'),
    'abantu': ('ntu', 'aba', 'MU-BA'),
    'ekitabo': ('tabo', 'eki', 'KI-BI'),
    'amazzi': ('zzi', 'ama', 'LI-MA'),
    'ente': ('te', 'en', 'N'),
    'oluggi': ('ggi', 'olu', 'LU-N'),
    'akagaali': ('gaali', 'aka', 'KA-BU'),
    'obulimi': ('limi', 'obu', 'BU'),
    'kikumi': ('kikumi', None, None),
}

# ---------- Step 6: Load test data ----------
def load_test_data(filename: str) -> Dict[str, Tuple[str, str, str]]:
    """Load tab separated data from a file."""
    if not os.path.exists(filename):
        print(f"⚠️  Data file not found: {filename}")
        print("   Using fallback minimal dataset.")
        return FALLBACK_DATA

    data = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 4:
                continue
            word, cls, prefix, root = parts
            if cls == 'FALSE':
                data[word] = (root, None, None)
            else:
                data[word] = (root, prefix, cls)

    if not data:
        print("⚠️  Data file is empty – using fallback dataset.")
        return FALLBACK_DATA

    print(f"✅ Loaded {len(data)} entries from {filename}")
    return data

# ---------- Step 7: Main test runner ----------
def run_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 60)
    print("TEST: Luganda Noun Stripper")
    print("=" * 60)

    # Load test data
    test_data = load_test_data(DATA_PATH)

    # Instantiate the stripper
    stripper = NounStripper()

    # Run tests
    total = len(test_data)
    passed = 0
    failed = 0
    failures = []

    for word, (exp_root, exp_prefix, exp_class) in test_data.items():
        root, prefix, cls = stripper.strip(word)

        root_ok = (root == exp_root)
        prefix_ok = (prefix == exp_prefix)
        class_ok = (cls == exp_class)

        if root_ok and prefix_ok and class_ok:
            passed += 1
        else:
            failed += 1
            failures.append((word, exp_root, root, exp_class, cls))

        # Show progress (only show failures for large datasets)
        if total <= 50 or not (root_ok and prefix_ok and class_ok):
            status = "✓" if root_ok and prefix_ok and class_ok else "✗"
            print(f"{status} {word:20} -> {root:12}  ({cls})")

    # Summary
    print("=" * 60)
    print(f"Total tests: {total}")
    print(f"✅ Passed: {passed}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
        print("\n--- Failures ---")
        for word, exp_root, got_root, exp_cls, got_cls in failures:
            print(f"  {word}: expected root '{exp_root}' (class {exp_cls}), got '{got_root}' (class {got_cls})")
    else:
        print("✅ All tests passed!")
    print("=" * 60)

    return passed, failed

# ---------- Step 8: Entry point ----------
if __name__ == "__main__":
    run_tests()
