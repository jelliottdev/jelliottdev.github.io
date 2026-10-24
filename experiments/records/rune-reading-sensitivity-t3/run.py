"""Check the pinned T1/T3 receipt; optionally rerun T3 from its MIT snapshot."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PINNED_STREAM_SHA = "023312066df471005264b9cbe7997cb77d2a9a6a2dc9b3316d22674023af1585"
SOURCE_OUTPUTS = ("out_baseline.json", "out_random.json", "out_targeted.json",
                  "out_decode_L120_LP1.json", "out_decode_L400_LP1.json",
                  "out_decode_L12956_KJV.json")


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def same(a, b, path="root"):
    if isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), path
        for key in a:
            if key != "secs":
                same(a[key], b[key], path + "." + key)
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, f"{path}[{i}]")
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        assert isinstance(b, (int, float)) and math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-12), (path, a, b)
    else:
        assert a == b, (path, a, b)


def verify_inputs():
    plan = read("plan.json")
    for item in plan["inputs"]:
        path = REPO / item["path"]
        assert sha(path.read_bytes()) == item["sha256"], path
    fullbook = read("fullbook-plan.json")
    assert fullbook["grid"]["k_book"] == [0, 50, 100, 200, 450, 900]
    assert sha((REPO / fullbook["kjv_source"]).read_bytes()) == fullbook["kjv_sha256"]
    assert sha((HERE / "worker-plan.json").read_bytes()) == plan["frozen_worker_plan_sha256"]
    manifest = read("source-snapshot-manifest.json")
    prereg = next(item for item in manifest["files"] if item["path"].endswith("/T3/PREREG.md"))
    assert prereg["sha256"] == plan["source_frozen_prereg_sha256"]
    with zipfile.ZipFile(HERE / "source-snapshot.zip") as archive:
        assert set(archive.namelist()) == {x["path"] for x in manifest["files"]}
        for item in manifest["files"]:
            raw = archive.read(item["path"])
            assert len(raw) == item["bytes"] and sha(raw) == item["sha256"], item["path"]
    return plan


def derive(plan):
    inp = read("input-snapshot.json")
    c = inp["stream"]
    changes = inp["oae450"]
    assert len(c) == 12956 and len(changes) == len({r["pos"] for r in changes}) == 450
    assert sha(",".join(map(str, c)).encode()) == PINNED_STREAM_SHA
    altered = c.copy()
    for r in changes:
        assert 0 <= r["pos"] < len(c) and 0 <= r["canon_idx"] < 29 and 0 <= r["alt_idx"] < 29
        assert c[r["pos"]] == r["canon_idx"]
        altered[r["pos"]] = r["alt_idx"]

    def doublets(seq):
        return sum(a == b for a, b in zip(seq, seq[1:]))

    def ioc29(seq):
        n = len(seq)
        return 29 * sum(v * (v - 1) for v in collections.Counter(seq).values()) / (n * (n - 1))

    baseline = read("out_baseline.json")
    target = read("out_targeted.json")
    random = read("out_random.json")
    assert baseline["pc3_pass"] and baseline["pc1_pass"]
    assert baseline["map_gate"]["n_mapped"] == 450
    assert doublets(c) == baseline["baseline"]["doublets"] == 86
    assert doublets(altered) == target["ALL450_exact"]["doublets"] == 103
    assert math.isclose(ioc29(c), baseline["baseline"]["ioc_norm"], abs_tol=1e-12)
    assert math.isclose(ioc29(altered), target["ALL450_exact"]["ioc_norm"], abs_tol=1e-12)
    assert target["n_located"] == 450
    assert random["trials"] == target["trials"] == 400

    decoder = {}
    for length, register in ((120, "LP1"), (400, "LP1"), (12956, "KJV")):
        d = read(f"out_decode_L{length}_{register}.json")
        assert d["gate_F0"]["pass"] and d["gate_F0"]["path_mismatches"] == 0
        if register == "LP1":
            assert d["rows"][0]["recovery_correct"]["median"] == 1
        else:
            assert d["reps"] == 6 and [r["k_book"] for r in d["rows"]] == [0, 50, 100, 200, 450, 900]
            same(read("out_decode_L12956_KJV.source.json"), d, "KJV source/fresh")
        decoder[str(length)] = {
            "register": register, "replicates_per_level": d["reps"], "levels": len(d["rows"]),
            "first_below_90pct_recovery_k_book": d["K_REC_k_book"],
            "first_score_overlap_k_book": d["K_SEP_k_book"],
            "at_450_recovery": next(x["recovery_correct"]["median"] for x in d["rows"] if x["k_book"] == 450),
        }

    gread = read("out_gread_lp2.json")["lp2"]
    loo = read("out_loo.json")
    adj = read("adjudication.json")
    corpus = read("out_corpus_lp2.json")
    assert (gread["n_correct"], gread["n_canon"]) == (180, 180)
    assert adj["n_records"] == len(adj["rows"]) == 450
    assert corpus["n_canon"] == 13136 and corpus["n_equal"] == 13088
    assert sum(loo["oae"]["recall_" + r]["of"] for r in ("O", "A", "AE")) == 1404

    floor_pct = random["floors"]["D-GER"][0]
    return {
        "plan_sha256": sha((HERE / "plan.json").read_bytes()),
        "source_revision": plan["source_revision"],
        "baseline": {"runes": len(c), "doublets": doublets(c),
                     "doublet_pct": baseline["baseline"]["doublet_rate_pct"],
                     "ioc29": ioc29(c)},
        "all_450_source_alternatives": {"doublets": doublets(altered),
                                         "doublet_pct": target["ALL450_exact"]["doublet_rate_pct"],
                                         "ioc29": ioc29(altered)},
        "source_german_comparison_floor_pct": floor_pct,
        "source_german_comparison_floor_doublets": math.ceil(floor_pct / 100 * (len(c) - 1)),
        "targeted_sample": {name: {"k": target[name]["rows"][-1]["k"],
                                   "median_doublet_pct": target[name]["rows"][-1]["stats"]["doublet_rate_pct"]["median"]}
                            for name in ("P-OAE450", "P-OAE450R", "P-OAEFAM")},
        "decoder_fixture": decoder,
        "source_reader_receipt": {"solved_control": "180/180 source-canon agreement",
                                  "oae_adjudication_rows": adj["n_records"],
                                  "whole_corpus_agreement": [corpus["n_equal"], corpus["n_canon"]],
                                  "training_limit": "Global canon-derived alignment and labels include test pages; these are transductive source-consistency checks, not independent image truth."},
        "limits": ["450 machine disagreements are possible alternatives, not verified errors",
                   "Decode corruption uses synthetic known-key LP1 or KJV passages, not actual LP2 plaintext",
                   "Full-book decoder fixture uses KJV plaintext, not LP1; passage length and text register both change",
                   "KJV source output hardcodes LP1_REAL in conditionals.register despite its top-level register=KJV"],
    }


def replay(jobs=1):
    with tempfile.TemporaryDirectory(prefix="liberpedia-t3-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(HERE / "source-snapshot.zip") as archive:
            archive.extractall(root)
        t3 = root / "liber-primus/analysis/round19/T3"
        for script, args in (("t3_baseline.py", []), ("t3_sensitivity.py", []),
                             ("t3_targeted.py", []), ("t3_decode.py", ["120", "120", "LP1"]),
                             ("t3_decode.py", ["400", "60", "LP1"])):
            result = subprocess.run([sys.executable, script, *args], cwd=t3,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, check=True)
            print(f"PASS source {script} {' '.join(args)}: {len(result.stdout.splitlines())} log lines")
        if jobs == 1:
            kjv = root / "liber-primus/data/kjv.txt"
            kjv.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / read("fullbook-plan.json")["kjv_source"], kjv)
            env = dict(os.environ, T3_KBOOK="0,50,100,200,450,900")
            subprocess.run([sys.executable, "t3_decode.py", "12956", "6", "KJV"],
                           cwd=t3, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, check=True)
        else:
            subprocess.run([sys.executable, str(HERE / "replay_fullbook_parallel.py"),
                            "--jobs", str(jobs), "--compare", str(HERE / "out_decode_L12956_KJV.json"),
                            "--output", str(t3 / "out_decode_L12956_KJV.json")], check=True)
        for filename in SOURCE_OUTPUTS:
            same(json.loads((t3 / filename).read_text()), read(filename), filename)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--replay", action="store_true", help="rerun full available T3 grids from the pinned MIT snapshot (several minutes)")
    ap.add_argument("--jobs", type=int, default=1,
                    help="1 uses the original full-book source process; 2–4 runs independent error levels in parallel")
    args = ap.parse_args()
    assert 1 <= args.jobs <= 4
    plan = verify_inputs()
    result = derive(plan)
    same(result, read("results.json"), "results.json")
    if args.replay:
        replay(args.jobs)
    print("PASS: hashes, source archive, direct rune arithmetic, reader and decoder receipts")


if __name__ == "__main__":
    main()
