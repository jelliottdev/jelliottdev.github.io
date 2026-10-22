"""Independent regex-based recount of the fixed LP2 short-lag profile."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
RESULT = json.loads((Path(__file__).resolve().parent / "results.json").read_text(encoding="utf-8"))
index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
alphabet = {entry["rune"] for entry in index["alphabet"]}
streams = []
for page in range(56):
    text = (ROOT / f"text/lp2-{page:02d}.txt").read_text(encoding="utf-8")
    stream = [match.group() for match in re.finditer(r"[\u16a0-\u16ff]", text)]
    assert all(rune in alphabet for rune in stream)
    streams.append(stream)
assert sum(map(len, streams)) == 12956
for row in RESULT["rows"]:
    lag = row["lag"]
    pairs = sum(max(len(stream) - lag, 0) for stream in streams)
    matches = sum(sum(stream[i] == stream[i + lag] for i in range(len(stream) - lag))
                  for stream in streams)
    expected = Fraction(0)
    for stream in streams:
        n = len(stream)
        if n < 2:
            continue
        counts = Counter(stream)
        expected += Fraction(max(0, n-lag) * sum(c*(c-1) for c in counts.values()), n*(n-1))
    assert (matches, pairs, str(expected)) == (
        row["matches"], row["pairs"], row["shuffle_expected_fraction"])
    print(f"lag {lag}: {matches}/{pairs}, shuffle expected {float(expected):.4f}")
print("PASS independent rune extraction, lag counts and exact shuffle expectations")
