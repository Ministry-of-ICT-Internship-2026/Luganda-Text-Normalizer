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

    # --- Numeral vocabulary (see numbers.py) -------------------------
    # Every atomic word numbers.number_to_words() can produce. Without
    # these, the noun/verb strippers mistake numeral morphology for
    # noun-class prefixes -- e.g. "mukaaga" (six) looks exactly like
    # MU-BA-class "mu" + root "kaaga", and would otherwise get wrongly
    # stripped to "kaaga". Compound-number connector words ("mu", "na")
    # are included too, even though the strippers already fall back
    # safely on those via their own "root too short" guards, so the
    # protection is explicit rather than incidental.
    'zeero', 'emu', 'bbiri', 'ssatu', 'nnya', 'ttaano',
    'mukaaga', 'musanvu', 'munaana', 'mwenda',
    'kkumi', 'amakumi', 'abiri', 'asatu', 'ana', 'ataano',
    'nkaaga', 'nsanvu', 'kinaana', 'kyenda',
    'kikumi', 'bikumi', 'lukumi', 'enkumi',
    'mu', 'na',
}