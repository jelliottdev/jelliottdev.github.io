"""Check the in-page width comparison against the published result JSON."""

import json
import re
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
results = json.loads((ROOT / "experiments/records/lp1-width-selection/results.json").read_text(encoding="utf-8"))
source = (ROOT / "experiments.js").read_text(encoding="utf-8")
match = re.search(r"const widthSelectionComparison\s*=\s*(\[[\s\S]*?\]);", source)
assert match, "Width-selection comparison data missing"
rows = json.loads(match.group(1))
assert rows == [list(item) for item in zip(results["widths"], results["observed_R"], results["fixed_width_tails"])], "Displayed values differ from results.json"
assert min(rows, key=lambda row: Fraction(row[1]))[0] == results["observed_winning_widths"][0]
assert min(rows, key=lambda row: row[2])[0] == 32
assert Fraction(results["selected_p"]) == Fraction(results["selected_tail"] + 1, results["plan"]["trials"] + 1)
assert f"{float(Fraction(results['selected_p'])):.5f}" in source
print("PASS: width comparison and selected tail match the published results")
