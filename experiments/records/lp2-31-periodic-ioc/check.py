"""Independent position-pair oracle for the scan; no simulation or network."""
import json
from run import ROOT, scan

alphabet = {a["rune"] for a in json.loads(
    (ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
stream = [c for c in (ROOT / "text/lp2-31.txt").read_text(encoding="utf-8")
          if c in alphabet]
for symbols in [list("ABABABAB"), list("AAAAAAAA"), stream]:
    for row in scan(symbols, range(2, min(21, len(symbols)))):
        k = row["period"]
        # Same residue means the distance between positions is a multiple of k.
        pairs = [(i, j) for i in range(len(symbols)) for j in range(i)
                 if (i - j) % k == 0]
        assert row["denominator"] == 2 * len(pairs)
        assert row["numerator"] == 2 * sum(symbols[i] == symbols[j] for i, j in pairs)
assert scan(list("ABABABAB"), [2])[0]["pooled_ioc"] == 1
print("Independent position-pair oracle agrees on controls and all LP2-31 periods.")
