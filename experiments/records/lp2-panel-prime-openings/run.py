"""Apply the sixteen LP2-15 spiral primes as a repeating rune shift."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def compute():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for entry in plan["inputs"]:
        assert sha(ROOT / entry["path"]) == entry["sha256"], entry["path"]
    ledger = json.loads((ROOT / "exports/fibonacci-prime-panel.json").read_text(encoding="utf-8"))
    key = [step["prime"] for step in ledger["rows"]]
    assert key == plan["key"] and len(key) == 16
    alphabet = [item["rune"] for item in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]]
    assert len(alphabet) == 29
    lookup = {rune: index for index, rune in enumerate(alphabet)}
    cases, lengths = [], {}
    for page in plan["pages"]:
        raw = (ROOT / "text" / (page + ".txt")).read_text(encoding="utf-8")
        stream = [lookup[c] for c in raw if c in lookup]
        lengths[page] = len(stream)
        for offset in plan["offsets"] if stream else []:
            for sign in plan["signs"]:
                output = [(value + sign * key[(i + offset) % 16]) % 29
                          for i, value in enumerate(stream)]
                matches = [item["id"] for item in plan["openings"]
                           if output[:12] == item["indices"]]
                cases.append({"page": page, "offset": offset, "sign": sign,
                              "output_indices": output, "matching_openings": matches})
    return {"schema": "liberpedia-panel-prime-openings-v1",
            "plan_sha256": sha(HERE / "plan.json"),
            "key": key, "key_mod_29": [n % 29 for n in key],
            "page_lengths": lengths, "empty_pages": [p for p, n in lengths.items() if n == 0],
            "case_count": len(cases), "comparison_count": len(cases) * len(plan["openings"]),
            "distinct_page_outputs": sum(len({tuple(c["output_indices"]) for c in cases if c["page"] == p}) for p in lengths),
            "matching_case_count": sum(bool(c["matching_openings"]) for c in cases),
            "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, separators=(",", ":"))
            handle.write("\n")
    print({k: result[k] for k in ("case_count", "comparison_count", "distinct_page_outputs", "matching_case_count", "empty_pages")})
