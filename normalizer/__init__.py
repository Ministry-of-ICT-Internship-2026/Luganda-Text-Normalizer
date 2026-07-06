"""
luganda_normalizer
===================
A small Python library for preprocessing Luganda text for NLP pipelines.

Currently provides:
    tokenize(text)  -- apostrophe-aware Luganda word tokenizer

Usage:
    from luganda_normalizer import tokenize
    tokenize("Abaana b'omu kibuga bazannya n'essanyu.")
"""

from .tokenizer import tokenize, diagnose

__all__ = ["tokenize", "diagnose"]
__version__ = "0.1.0"
