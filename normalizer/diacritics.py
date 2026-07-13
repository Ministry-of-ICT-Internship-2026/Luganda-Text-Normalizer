"""
P1 — Text Normalization: normalize_diacritics()
=================================================

Maps confirmed diacritic/spelling variants to one canonical form.

DESIGN PRINCIPLE (see P1_Research_Document.docx, section 4):
Only variants EXPLICITLY CONFIRMED by a native/fluent Luganda speaker are
ever merged. This is an explicit lookup table, not a generic "strip all
diacritics" rule — a blanket rule is exactly how you accidentally collapse
two different words into one, which silently breaks every module downstream
of P1. If a pair isn't in CONFIRMED_VARIANTS, this function leaves it alone.

Current status: CONFIRMED_VARIANTS is empty. The one candidate found so far
(ŋ vs "ng'", log #9 / Diacritic Variant Summary sheet) is still pending
native-speaker review and is listed under PENDING_REVIEW for visibility only
— it is NOT applied. Do not move an entry from PENDING_REVIEW to
CONFIRMED_VARIANTS without a recorded native-speaker decision.
"""

import unicodedata

# ---------------------------------------------------------------------------
# CONFIRMED_VARIANTS: variant -> canonical form.
# Populate this only after a native speaker has verified the pair really is
# the same word, just spelled differently (not two different words).
#
# Example of what a confirmed entry will look like once reviewed:
#   "ŋŋ": "ng'",   # confirmed [name/date]: gemination of ŋ is written ng' in
#                   # standard orthography, same word, no meaning distinction
# ---------------------------------------------------------------------------
CONFIRMED_VARIANTS: dict[str, str] = {
    # (intentionally empty — see module docstring)
}

# ---------------------------------------------------------------------------
# PENDING_REVIEW: candidates found during corpus inspection, NOT yet applied.
# Kept here (rather than only in the spreadsheet) so anyone reading this code
# sees exactly what's been deferred and why, right next to where a careless
# fix could otherwise be added.
# ---------------------------------------------------------------------------
PENDING_REVIEW = [
    {
        "forms": ["ŋŋ", "ng'"],
        "log_ref": "Research Log #9 / Diacritic Variant Summary",
        "example": "biddiriŋŋana / bakuŋŋaanye  vs  ng'ekitongole / ng'ali / ng'amulamusa",
        "question": "Are ŋŋ and ng' interchangeable spellings of the same "
                    "word, or does ŋŋ mark a distinct sound/length that "
                    "must not be merged with ng'?",
        "status": "pending native speaker review",
    },
]


def normalize_diacritics(text: str) -> str:
    """Apply only confirmed variant -> canonical mappings.

    Safe to call at any point in the project's life: with an empty
    CONFIRMED_VARIANTS table (current state), this is a no-op and returns
    the input unchanged aside from NFC normalization (encoding-level, not
    linguistic — see clean_text.normalize_unicode for why that's separate
    from a "real" spelling decision).
    """
    text = unicodedata.normalize("NFC", text)
    for variant, canonical in CONFIRMED_VARIANTS.items():
        text = text.replace(variant, canonical)
    return text


def list_pending_reviews() -> list[dict]:
    """Return the queue of unresolved variant candidates awaiting a native
    speaker's decision — useful for generating a review checklist/agenda.
    """
    return [item for item in PENDING_REVIEW if item["status"] != "confirmed"]


def add_confirmed_variant(variant: str, canonical: str, log_ref: str = "") -> None:
    """Explicit, deliberate way to add a confirmed mapping after review —
    prefer this over editing CONFIRMED_VARIANTS by hand mid-pipeline, so
    additions are always a conscious, traceable action.
    """
    CONFIRMED_VARIANTS[variant] = canonical