"""Independent direct-pair census for the section statistics."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = {entry["rune"] for entry in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
pages = {}
for n in range(56):
    source = (ROOT / "text" / f"lp2-{n:02d}.txt").read_text(encoding="utf-8")
    pages[n] = re.findall("[" + "".join(sorted(alphabet)) + "]", source)
for row in saved["groups"]:
    match = re.fullmatch(r"LP2-(\d\d)–(\d\d)", row["pages"])
    if not match:
        raise AssertionError(row["pages"])
    start, end = map(int, match.groups())
    group_pages = [pages[n] for n in range(start, end + 1)]
    runes = [r for page in group_pages for r in page]
    # Count ordered equal pairs by explicit position comparison, independent of Counter.
    collision = 2 * sum(runes[i] == runes[j] for i in range(len(runes)) for j in range(i + 1, len(runes)))
    edges = sum(max(0, len(page) - 1) for page in group_pages)
    doublets = sum(a == b for page in group_pages for a, b in zip(page, page[1:]))
    assert (len(runes), collision, edges, doublets) == (row["runes"], row["ioc_equal_ordered_pairs"], row["within_page_edges"], row["doublets"])
assert sum(row["doublets"] for row in saved["groups"]) == 86
assert sum(row["runes"] for row in saved["groups"]) == 12956
print("PASS independent section census")
