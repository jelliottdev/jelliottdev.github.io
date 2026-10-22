"""Check that the page index describes the published page records accurately."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["pages"]
assert len(index) == 75
assert len({item["id"] for item in index}) == 75

for item in index:
    page = json.loads((ROOT / "data/pages" / f"{item['id']}.json").read_text(encoding="utf-8"))
    assert item["has_reading"] == bool(page["reading"]), item["id"]
    assert item["has_notes"] == bool(page["notes"]), item["id"]
    assert item["status"] == page["status"], item["id"]
    assert item["status_basis"] == page["status_basis"], item["id"]
    assert (page["reviewed_text"] is not None) == bool(page["reviewed_text"]), item["id"]

status = Counter((item["release"], item["status"]) for item in index)
assert status == {("LP1", "solved"): 17, ("LP2", "unsolved"): 56, ("LP2", "solved"): 2}
assert {item["id"] for item in index if item["status"] == "solved" and not item["has_reading"]} == {"lp1-00", "lp1-02"}
assert all(item["has_notes"] for item in index)
assert sum(item["has_reading"] for item in index) == 17
reviewed = {item["id"] for item in index if json.loads((ROOT / "data/pages" / f"{item['id']}.json").read_text(encoding="utf-8"))["reviewed_text"] is not None}
assert reviewed == {"lp1-10", "lp2-05", "lp2-07", "lp2-11", "lp2-15", "lp2-35", "lp2-37", "lp2-38"}

print("75 page flags agree with records; 19 status-solved, 17 decoded readings, 75 notes, 8 reviewed derivatives.")
