"""
Pytest coverage for the Sprint 3 "Performance check" checklist item.

Complements check_performance.py (the manual/reporting script) with
automated assertions that:
  - large inputs complete within a sane time bound (regression guard
    against an accidental O(n^2) change, e.g. someone swapping the
    dict-lookup approach for repeated regex.search calls),
  - runtime scales roughly linearly with input size,
  - correctness holds on large input (round-trip word count, no crash,
    no truncation),
  - deeply repeated/pathological punctuation ("!!!!!!!!!!") doesn't
    cause slowdown -- the classic catastrophic-backtracking trigger
    for regex-based implementations.

Run: pytest test_performance.py -v
"""

import time

import pytest

from standardize_spelling import load_dictionary, standardize_spelling
from check_performance import make_text, time_run

MAPPINGS = load_dictionary()


@pytest.mark.parametrize("size", [1_000, 10_000, 100_000])
def test_completes_within_time_budget(size):
    """Generous upper bound (not a tight benchmark) that would fail hard
    if the implementation regressed to quadratic behavior."""
    text = make_text(size)
    elapsed = time_run(text, MAPPINGS)
    # Linear implementation does ~500k-1M words/sec; budget is deliberately
    # loose (10k words/sec floor) so this is robust across slow CI runners.
    budget = size / 10_000
    assert elapsed < budget, (
        f"{size} words took {elapsed:.3f}s, expected under {budget:.3f}s"
    )


def test_scaling_is_roughly_linear():
    """10x more input should take roughly 10x longer, not 100x (quadratic)
    or worse. Uses a generous multiplier to avoid flaky failures from
    timing noise while still catching real algorithmic regressions."""
    small_text = make_text(10_000)
    large_text = make_text(100_000)

    small_time = time_run(small_text, MAPPINGS)
    large_time = time_run(large_text, MAPPINGS)

    if small_time == 0:
        pytest.skip("timer resolution too coarse to measure small input")

    ratio = large_time / small_time
    # Input grew 10x; allow up to 25x runtime growth before flagging
    # non-linear behavior (comfortable margin over the expected ~10x).
    assert ratio < 25, f"runtime scaled {ratio:.1f}x for a 10x input increase"


def test_no_slowdown_on_pathological_punctuation():
    """Classic catastrophic-backtracking trigger for regex-based
    implementations: long runs of ambiguous punctuation. Since this
    module uses plain string scanning (not regex), this should be just
    as fast as normal text -- this test guards against a future regex
    based rewrite reintroducing that risk."""
    pathological_word = "!" * 5_000 + "webale" + "." * 5_000
    text = " ".join([pathological_word] * 200)

    start = time.perf_counter()
    result = standardize_spelling(text, MAPPINGS)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"pathological input took {elapsed:.3f}s -- possible backtracking"
    assert "webaale" in result  # still normalized correctly, not just fast


def test_large_input_no_words_silently_dropped():
    """Correctness check alongside the perf check: large input shouldn't
    silently drop or merge words. Word count can legitimately *increase*
    (e.g. 'oliotya' -> 'oli otya' is a one-to-two mapping) but must never
    decrease, since that would mean words got merged or lost."""
    size = 50_000
    text = make_text(size)
    result = standardize_spelling(text, MAPPINGS)
    assert len(result.split(" ")) >= size


def test_large_input_does_not_raise():
    text = make_text(200_000)
    # Should complete without exceptions of any kind.
    standardize_spelling(text, MAPPINGS)
