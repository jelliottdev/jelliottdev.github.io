"""Independently compare the fresh full-book KJV receipt with pinned source rows."""
import hashlib
import json
import math
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def compare(saved, fresh, location="$", ignored=("secs",)):
    if isinstance(saved, dict):
        assert isinstance(fresh, dict) and set(saved) == set(fresh), location
        for key in saved:
            if key not in ignored:
                compare(saved[key], fresh[key], location + "." + key)
    elif isinstance(saved, list):
        assert isinstance(fresh, list) and len(saved) == len(fresh), location
        for i, (a, b) in enumerate(zip(saved, fresh)):
            compare(a, b, f"{location}[{i}]")
    elif isinstance(saved, (int, float)) and not isinstance(saved, bool):
        assert math.isclose(saved, fresh, abs_tol=1e-12, rel_tol=1e-12), (location, saved, fresh)
    else:
        assert saved == fresh, (location, saved, fresh)


def main():
    plan_bytes = (HERE / "fullbook-plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    assert plan["grid"]["k_book"] == [0, 50, 100, 200, 450, 900]
    assert sha((REPO / plan["kjv_source"]).read_bytes()) == plan["kjv_sha256"]
    with zipfile.ZipFile(HERE / "source-snapshot.zip") as archive:
        assert sha(archive.read(plan["source_script"])) == plan["source_script_sha256"]
    saved_bytes = (HERE / "out_decode_L12956_KJV.source.json").read_bytes()
    fresh_bytes = (HERE / "out_decode_L12956_KJV.json").read_bytes()
    assert sha(saved_bytes) == plan["source_saved_output_sha256"]
    saved, fresh = json.loads(saved_bytes), json.loads(fresh_bytes)
    assert fresh["L"] == 12956 and fresh["reps"] == 6 and fresh["register"] == "KJV"
    assert fresh["gate_F0"]["pass"] and fresh["gate_F0"]["path_mismatches"] == 0
    assert [r["k_book"] for r in fresh["rows"]] == plan["grid"]["k_book"]
    assert fresh["K_REC_k_book"] == 450 and fresh["K_SEP_k_book"] == 900
    compare(saved, fresh)
    print("PASS: six full-book KJV levels, F0, source-output parity except elapsed seconds")


if __name__ == "__main__":
    main()
