"""Independent row reconstruction and inverse arithmetic for panel-prime stream."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
assert sha(HERE / "plan.json") == result["plan_sha256"]
for entry in plan["inputs"]:
    assert sha(ROOT / entry["path"]) == entry["sha256"], entry["path"]
panel = json.loads((ROOT / "data/pages/lp2-15.json").read_text(encoding="utf-8"))["numbers"]
ledger = json.loads((ROOT / "exports/fibonacci-prime-panel.json").read_text(encoding="utf-8"))
key = []
for step in ledger["rows"]:
    printed = panel[step["row"] - 1][step["column"] - 1]
    assert abs(3301 - step["prime"]) == printed == step["printed"]
    key.append(step["prime"])
assert key == plan["key"] == result["key"]
assert [n % 29 for n in key] == result["key_mod_29"]
assert len(set(result["key_mod_29"])) == 13
baseline = json.loads((HERE.parent / "lp2-fibonacci-openings/plan.json").read_text(encoding="utf-8"))
for field in ("pages", "signs", "prefix_length", "openings", "representation", "advancement", "decision", "stopping_rule"):
    assert plan[field] == baseline[field], field
alphabet = [r["rune"] for r in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]]
streams = {page: [alphabet.index(c) for c in (ROOT / "text" / (page + ".txt")).read_text(encoding="utf-8") if c in alphabet]
           for page in plan["pages"]}
assert result["page_lengths"] == {p: len(s) for p, s in streams.items()}
assert result["empty_pages"] == [p for p, s in streams.items() if not s]
for opening in plan["openings"]:
    with (ROOT / opening["source"]).open(encoding="utf-8", newline="") as handle:
        assert [int(row["output_index"]) for row in list(csv.DictReader(handle))[:12]] == opening["indices"]
expected = {(p, o, s) for p, stream in streams.items() if stream
            for o in plan["offsets"] for s in plan["signs"]}
seen, matched = set(), 0
for case in result["cases"]:
    ident = case["page"], case["offset"], case["sign"]
    assert ident in expected and ident not in seen
    seen.add(ident)
    raw = streams[case["page"]]
    output = case["output_indices"]
    assert len(output) == len(raw)
    assert all((value - case["sign"] * key[(i + case["offset"]) % 16]) % 29 == raw[i]
               for i, value in enumerate(output))
    matches = [item["id"] for item in plan["openings"] if output[:12] == item["indices"]]
    assert matches == case["matching_openings"]
    matched += bool(matches)
assert seen == expected
assert result["case_count"] == len(expected) == 1760
assert result["comparison_count"] == 15840
assert result["matching_case_count"] == matched
assert result["distinct_page_outputs"] == sum(len({tuple(c["output_indices"]) for c in result["cases"] if c["page"] == p}) for p in streams)
print("PASS: 16 panel-derived primes, 1760 inverse-checked outputs and 15,840 opening comparisons")
