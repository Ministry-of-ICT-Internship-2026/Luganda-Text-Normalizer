"""
stopwords.py – closed-class Luganda words (conjunctions, quantifiers,
particles) that must never be noun- or verb-stripped, even if they
happen to start with a string that matches a known prefix.

Small and expected to grow — add words here as you discover more
false positives during testing, same pattern as FALSE_POSITIVES in
morphology_nouns.py, just shared across both strippers.
"""

CLOSED_CLASS = {
    'nga',      # while / as / like
    'nti',      # that (complementizer)
    'oba',      # or / whether
    'naye',     # but
    'anti',     # but / well
    'kubanga',  # because
    'wabula',   # however
    'abamu',    # some (people) — quantifier, not a MU-BA plural noun
    'bonna',    # all
    'bombi',    # both
    'buli',     # every
}