"""Compare a fresh exact T3 KJV full-book replay with the pinned source output."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[4]
ROOT = WORK / "research-wiki"
SOURCE = WORK / "t1-source-replay-20261023" / "liber-primus"
FRESH = WORK / "t3-kjv-fullbook-20261023" / "liber-primus"
REL = Path("analysis/round19/T3/out_decode_L12956_KJV.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same(a, b, loc="$", ignored=("secs",)):
    if isinstance(a, dict):
        assert isinstance(b, dict), loc
        assert set(a) == set(b), (loc, set(a) ^ set(b))
        for key in a:
            if key not in ignored:
                same(a[key], b[key], loc + "." + key)
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), loc
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, f"{loc}[{i}]")
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        assert math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-12), (loc, a, b)
    else:
        assert a == b, (loc, a, b)


def main():
    plan = json.loads((HERE / "fullbook-plan.json").read_text(encoding="utf-8"))
    assert sha(HERE / "fullbook-plan.json") == "809a353ee246dc745ac7235ad4793d82b660106417a80d7e3a24cf1a2b3d0dd0"
    assert sha(ROOT / plan["kjv_source"]) == plan["kjv_sha256"]
    assert sha(FRESH / "data/kjv.txt") == plan["kjv_sha256"]
    assert sha(FRESH / plan["source_script"].removeprefix("liber-primus/")) == plan["source_script_sha256"]
    assert sha(SOURCE / REL) == plan["source_saved_output_sha256"]
    saved = json.loads((SOURCE / REL).read_text(encoding="utf-8"))
    fresh_path = FRESH / REL
    fresh = json.loads(fresh_path.read_text(encoding="utf-8"))
    assert fresh["L"] == 12956 and fresh["reps"] == 6 and fresh["register"] == "KJV"
    assert fresh["gate_F0"]["pass"] and fresh["gate_F0"]["path_mismatches"] == 0
    assert [r["k_book"] for r in fresh["rows"]] == plan["grid"]["k_book"]
    assert fresh["K_REC_k_book"] == 450 and fresh["K_SEP_k_book"] == 900
    same(saved, fresh)
    print(json.dumps({"status": "PASS", "fresh_output_sha256": sha(fresh_path),
                      "saved_source_sha256": sha(SOURCE / REL),
                      "levels": len(fresh["rows"]), "replicates_per_level": fresh["reps"],
                      "K_REC_k_book": fresh["K_REC_k_book"],
                      "K_SEP_k_book": fresh["K_SEP_k_book"]}))


if __name__ == "__main__":
    main()
