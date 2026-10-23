#!/usr/bin/env python3
"""Freeze the grid-prefix key and opening-test corpus before scoring."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json"
GRID = ROOT / "exports/alphanumeric-grids.json"
ABC = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"


def pin(path):
    data = (ROOT / path).read_bytes()
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def main():
    if (HERE / "plan.json").exists():
        raise SystemExit("Frozen plan exists; refusing overwrite")
    source_plan = json.loads(SOURCE.read_text(encoding="utf8"))
    grid = json.loads(GRID.read_text(encoding="utf8"))
    records = grid["records"]
    assert len(records) == 256 and [x["sequence"] for x in records] == list(range(1, 257))
    tokens = [x["token"] for x in records]
    assert all(len(x) == 2 and x[0] in "01234" and x[1] in ABC for x in tokens)
    channels = [{"prefix": prefix, "suffixes": "".join(x[1] for x in tokens if x[0] == prefix)}
                for prefix in "01234"]
    assert [len(x["suffixes"]) for x in channels] == [60, 58, 65, 56, 17]
    assert channels[-1]["suffixes"] == "97DEF756B98A80EB9"
    assert all(c in "0123456789ABCDEF" for c in channels[-1]["suffixes"])
    pages = []
    alphabet = {x["rune"] for x in json.loads((ROOT / "data/index.json").read_text(encoding="utf8"))["alphabet"]}
    for pid in source_plan["pages"]:
        path = f"text/{pid}.txt"
        if sum(c in alphabet for c in (ROOT / path).read_text(encoding="utf8")):
            pages.append({"id": pid, **pin(path)})
    assert len(pages) == 55 and "lp2-50" not in [x["id"] for x in pages]
    openings = [{"id": x["id"], "indices": x["indices"], "source": x["source"], "sha256": x["sha256"]}
                for x in source_plan["openings"]]
    assert len(openings) == 9 and all(len(x["indices"]) == 12 for x in openings)
    for o in openings:
        assert hashlib.sha256((ROOT / o["source"]).read_bytes()).hexdigest() == o["sha256"]
    plan = {
        "schema": "liberpedia-grid-prefix-split-openings-plan-v1",
        "question": "Do manuscript-order suffix channels from the LP2-49–51 grid act as repeating GP29 keys for a known opening at the start of another LP2 page?",
        "source_grid": pin("exports/alphanumeric-grids.json"),
        "source_opening_plan": pin("experiments/records/lp2-known-vigenere-keys/plan.json"),
        "rune_alphabet": pin("data/index.json"),
        "base60_alphabet": ABC,
        "channel_order": "Grid sequence 1–256, retaining each token's suffix in its own leading-digit class 0–4",
        "channels": channels,
        "mappings": ["base60-digit-mod29", "ascii-byte-mod29", "group4-hex-nibble"],
        "decode": "For each selected key, P[j] = C[j] + sign*K[(j+phase) mod key_length] mod 29; signs -1 and +1; all phases 0..key_length-1.",
        "comparison": "First twelve runes of each nonempty LP2-00–55 page against all nine fixed 12-rune opening vectors, exact equality. Headings included, non-rune layout ignored, page starts fresh.",
        "pages": pages,
        "openings": openings,
        "excluded": "The source proposal's five-state direction table, origin, boundary and route readout are unspecified and are not simulated. The 17 hex nibbles are tested as 17 values, never padded or packed into fabricated bytes. No later-position crib or language scoring.",
        "declared_before_run": "2026-10-23"
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("Frozen channels", [len(x["suffixes"]) for x in channels], "; 55 pages; 9 openings")


if __name__ == "__main__":
    main()
