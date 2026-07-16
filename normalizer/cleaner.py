"""
Performance check for standardize_spelling.py (Sprint 3 checklist item).
 
This module uses NO regular expressions anywhere -- all matching is plain
string scanning (str indexing/slicing) and dict lookups, both O(n) in the
length of the input. There is therefore no possibility of catastrophic
regex backtracking. This script instead verifies, empirically, that
runtime scales linearly with input size (not quadratically or worse),
and reports throughput on a large synthetic document.
 
Run: python3 check_performance.py
"""
 
import random
import time
 
from standardize_spelling import load_dictionary, standardize_spelling
 
WORD_POOL = [
    "sebo", "nyabo", "webale", "oliotya", "bulunji", "neda", "mpora",
    "cente", "abana", "saawa", "kubanga", "gyebaleko", "twagala",
    "(webale).", '"nedda,', "bulung'i", "unmapped_word", "gyebaleko!",
]
 
 
def make_text(n_words: int) -> str:
    random.seed(42)
    return " ".join(random.choice(WORD_POOL) for _ in range(n_words))
 
 
def time_run(text: str, mappings: dict) -> float:
    start = time.perf_counter()
    standardize_spelling(text, mappings)
    return time.perf_counter() - start
 
 
def main():
    mappings = load_dictionary()
    sizes = [1_000, 10_000, 100_000, 500_000]
    timings = []
 
    print("Linear-scaling check (no regex, so this should scale ~O(n)):\n")
    print(f"{'words':>10} | {'time (s)':>10} | {'ratio vs prev':>14}")
    print("-" * 40)
 
    prev_time = None
    prev_size = None
    for size in sizes:
        text = make_text(size)
        elapsed = time_run(text, mappings)
        timings.append(elapsed)
        ratio_str = "--"
        if prev_time is not None and prev_time > 0:
            size_ratio = size / prev_size
            time_ratio = elapsed / prev_time
            ratio_str = f"{time_ratio:.2f}x (input {size_ratio:.0f}x)"
        print(f"{size:>10} | {elapsed:>10.4f} | {ratio_str:>14}")
        prev_time, prev_size = elapsed, size
 
    # A quadratic (or worse) implementation would show time-ratio >>
    # size-ratio as input grows. Flag if the last step looks non-linear.
    last_size_ratio = sizes[-1] / sizes[-2]
    last_time_ratio = timings[-1] / timings[-2] if timings[-2] > 0 else 0
    print()
    if last_time_ratio > last_size_ratio * 2:
        print("WARNING: runtime growth outpaces input growth -- investigate.")
    else:
        print("OK: runtime growth tracks input growth (linear, as expected).")
 
    words_per_sec = sizes[-1] / timings[-1]
    print(f"\nThroughput on {sizes[-1]:,}-word input: {words_per_sec:,.0f} words/sec")
 
 
if __name__ == "__main__":
    main()
 
