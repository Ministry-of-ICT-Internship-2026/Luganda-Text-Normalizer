# test_pipeline.py
import sys
sys.path.insert(0, ".")
from normalizer.pipeline import normalize

with open("data/sample_corpus.txt", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]

for line in lines:
    print("IN :", line)
    print("OUT:", normalize(line))
    print()