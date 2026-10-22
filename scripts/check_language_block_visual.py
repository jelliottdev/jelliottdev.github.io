"""Check the compact language comparison against the saved block results."""

import ast
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "experiments.js").read_text(encoding="utf-8")
match = re.search(r"const languageBlockSummary=\{(.*?)\n\};", source, re.S)
assert match, "language summary is missing"
literal = "{" + re.sub(r"(?m)^\s*(letters|folded):", r"'\1':", match.group(1)) + "}"
shown = ast.literal_eval(literal)
saved = json.loads((ROOT / "experiments/records/parallel-language-blocks/results.json").read_text(encoding="utf-8"))

assert set(shown) == set(saved["modes"])
for mode, rows in shown.items():
    blocks = saved["modes"][mode]["blocks"]
    expected_names = {item["language"] for item in blocks[0]["ranking"]}
    assert {row[0] for row in rows} == expected_names
    assert len(rows) == len(expected_names) == 8
    for language, median, minimum, maximum in rows:
        values = [next(item["length_tv"] for item in block["ranking"] if item["language"] == language) for block in blocks]
        expected = (statistics.median(values), min(values), max(values))
        assert all(abs(display - actual) < 0.0000051 for display, actual in zip((median, minimum, maximum), expected)), (mode, language)

print("PASS: all 24 displayed language summaries match eight-block source data")
