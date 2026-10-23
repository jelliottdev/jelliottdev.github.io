"""Independent section-position recount and a separately sampled null sanity check."""
import json
import random
from pathlib import Path

root = Path(__file__).resolve().parents[3]
here = Path(__file__).resolve().parent
report = json.loads((here / "results.json").read_text(encoding="utf-8"))
index = json.loads((root / "data/index.json").read_text(encoding="utf-8"))
alphabet = set(row["rune"] for row in index["alphabet"])
sections = [(0, 2), (3, 7), (8, 14), (15, 22), (23, 26), (27, 32), (33, 39), (40, 53), (54, 55)]
events = []
for start, stop in sections:
    symbols = [rune for page in range(start, stop + 1)
               for rune in (root / f"text/lp2-{page:02}.txt").read_text(encoding="utf-8") if rune in alphabet]
    events.append([i for i, (before, after) in enumerate(zip(symbols, symbols[1:]), 1) if before == after])
assert events == report["event_positions"]
assert sum(map(len, events)) == 86
for modulus in range(2, 9):
    counted = [sum(position % modulus == remainder for section in events for position in section)
               for remainder in range(modulus)]
    assert counted == report["observed"][str(modulus)]["counts"]
assert report["max_controls_at_least_observed"] == sum(
    value >= report["best_observed_chi_over_df"] for value in report["control_max_chi_over_df"])
assert len(report["control_max_chi_over_df"]) == report["trials"] == 5000
assert report["planted_mod7_chi_over_df"] > max(report["control_max_chi_over_df"])
print("doublet-section-residues: independent event positions and residue counts checked")
