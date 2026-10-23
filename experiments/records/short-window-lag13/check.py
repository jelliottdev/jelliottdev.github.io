"""Independent source extraction and direct-position checks for short-window recurrence."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = {item["rune"] for item in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
pattern = re.compile("[" + "".join(sorted(alphabet)) + "]")
pages = [pattern.findall((ROOT / "text" / f"lp2-{i:02d}.txt").read_text(encoding="utf-8")) for i in range(56)]

def direct(page, lag):
    return sum(1 for start in range(len(page) - lag - 1)
               if page[start:start+2] == page[start+lag:start+lag+2])

assert direct(list("ABCDEFGHIJKLMAB"), 13) == 1
assert direct(list("ABCDEFGHIJKLMAB"), 12) == 0
assert sum(len(page) for page in pages) == saved["runes"] == 12956
assert sum(max(0, len(page)-14) for page in pages) == saved["lag13"]["windows"]
for lag in range(2, 29):
    assert sum(direct(page, lag) for page in pages) == saved["lag_scan"]["counts"][str(lag)]
assert saved["lag_scan"]["counts"]["13"] == saved["lag13"]["two_pair_matches"]
print("PASS independent direct-position lag scan")
