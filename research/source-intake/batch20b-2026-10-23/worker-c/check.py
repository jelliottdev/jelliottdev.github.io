"""Check fresh T3 outputs against the pinned source and direct rune arithmetic."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import subprocess
from pathlib import Path

REV = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
SOURCE = "liber-primus/analysis/round19/T3/"


def same(a, b, path="root"):
    if isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), path
        for key in a:
            if key != "secs":  # wall time is deliberately not reproducible
                same(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, f"{path}[{i}]")
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        assert isinstance(b, (int, float)) and math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-12), (path, a, b)
    else:
        assert a == b, (path, a, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-repo", type=Path, required=True)
    args = ap.parse_args()
    here = Path(__file__).resolve().parent
    data = here / "evidence"
    receipt = json.loads((here / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["source_revision"] == REV
    for entry in receipt["entries"]:
        for item in entry["evidence"]:
            raw = (here.parents[3] / item["path"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item["sha256"], item["path"]

    for filename in ("out_baseline.json", "out_random.json", "out_targeted.json",
                     "out_decode_L120_LP1.json", "out_decode_L400_LP1.json"):
        fresh = json.loads((data / filename).read_text(encoding="utf-8"))
        source = json.loads(subprocess.check_output(
            ["git", "show", f"{REV}:{SOURCE}{filename}"], cwd=args.source_repo))
        same(fresh, source, filename)

    snapshot = json.loads((data / "input-snapshot.json").read_text(encoding="utf-8"))
    cipher, changes = snapshot["stream"], snapshot["oae450"]
    assert len(cipher) == 12956 and len(changes) == len({r["pos"] for r in changes}) == 450
    assert hashlib.sha256(",".join(map(str, cipher)).encode()).hexdigest() == (
        "023312066df471005264b9cbe7997cb77d2a9a6a2dc9b3316d22674023af1585")
    changed = cipher.copy()
    for row in changes:
        pos = row["pos"]
        assert 0 <= pos < len(cipher)
        assert 0 <= row["canon_idx"] < 29 and 0 <= row["alt_idx"] < 29
        assert cipher[pos] == row["canon_idx"]
        changed[pos] = row["alt_idx"]

    def doublets(seq):
        return sum(x == y for x, y in zip(seq, seq[1:]))

    def ioc_norm(seq):
        counts = collections.Counter(seq)
        n = len(seq)
        return 29 * sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))

    baseline = json.loads((data / "out_baseline.json").read_text(encoding="utf-8"))
    targeted = json.loads((data / "out_targeted.json").read_text(encoding="utf-8"))
    assert baseline["pc3_pass"] and baseline["pc1_pass"]
    assert baseline["map_gate"]["n_mapped"] == 450
    assert doublets(cipher) == baseline["baseline"]["doublets"] == 86
    assert doublets(changed) == targeted["ALL450_exact"]["doublets"] == 103
    assert math.isclose(ioc_norm(cipher), baseline["baseline"]["ioc_norm"], abs_tol=1e-12)
    assert math.isclose(ioc_norm(changed), targeted["ALL450_exact"]["ioc_norm"], abs_tol=1e-12)
    for length in (120, 400):
        dec = json.loads((data / f"out_decode_L{length}_LP1.json").read_text(encoding="utf-8"))
        assert dec["gate_F0"]["pass"] and dec["gate_F0"]["path_mismatches"] == 0
        assert dec["rows"][0]["recovery_correct"]["median"] == 1.0
        assert dec["rows"][0]["separated"]
    print("PASS: source output parity, evidence hashes, and direct doublet/IoC arithmetic")


if __name__ == "__main__":
    main()
