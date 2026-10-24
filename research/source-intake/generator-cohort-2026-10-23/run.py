#!/usr/bin/env python3
"""Recount the frozen, bounded generator cohort. No manuscript search."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def run(source, temp):
    assert PLAN["source_revision"] == subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    hashes = {}
    for item in PLAN["inputs"]:
        path = item["path"]
        raw = subprocess.check_output(
            ["git", "-C", str(source), "show", f'{PLAN["source_revision"]}:{path}']
        )
        digest = hashlib.sha256(raw).hexdigest()
        assert len(raw) == item["bytes"] and digest == item["sha256"], path
        target = temp / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        hashes[path] = digest
    # A2's Latin transliteration reducer imports this source dependency.
    # It was omitted from the frozen plan; record it as a transparent addendum.
    extra_path = "liber-primus/src/lp/gematria.py"
    extra_raw = subprocess.check_output(
        ["git", "-C", str(source), "show", f'{PLAN["source_revision"]}:{extra_path}']
    )
    extra_target = temp / extra_path
    extra_target.parent.mkdir(parents=True, exist_ok=True)
    extra_target.write_bytes(extra_raw)
    extra_hash = hashlib.sha256(extra_raw).hexdigest()
    sys.path.insert(0, str(temp / "liber-primus/src"))
    base = temp / "liber-primus/analysis"
    g1dir = base / "round19/G1"
    sys.path.insert(0, str(g1dir))
    g1 = module("g1_keystream", g1dir / "keystream.py")
    v1 = json.loads((g1dir / "validation.json").read_text())
    mismatches = []
    count = 0
    for name, seeds in v1["test_vectors"].items():
        if name in ("openssl_enc_rc4_k", "shuf_random_source") or name not in g1.REGISTRY:
            continue
        _, make, _ = g1.REGISTRY[name]
        for seed, expected in seeds.items():
            if expected is None:  # source has no saved Bash 4.0 vector for two seeds
                continue
            actual = list(make(int(seed), len(expected)))
            if name == "mrand48":  # source oracle renders signed 32-bit C long
                actual = [x - 2**32 if x >= 2**31 else x for x in actual]
            count += 1
            if actual != expected:
                mismatches.append([name, seed, expected, actual])
    assert count == 134 and not mismatches, mismatches[:2]

    g2dir = base / "round19/G2"
    g2 = module("g2_gen_perl", g2dir / "gen_perl.py")
    v2 = json.loads((g2dir / "validation.json").read_text())
    counts = {k: 0 for k in ("A0", "A1", "A2")}
    for row in v2["gate_A"]["rows"]:
        gate, seed = row["gate"], row["seed"]
        if gate == "A0":
            rng = g2.Drand48(seed)
            actual = [format(rng.drand48(), ".17g") for _ in range(3)]
            expected = row["first3_perl"]
        elif gate == "A1":
            m = int(re.search(r"rand\((\d+)\)", row["what"]).group(1))
            actual = list(g2.int_rand_stream(seed, m, 8))
            expected = row["first8_perl"]
        else:
            actual = list(g2.make_ks(row["what"], seed, 8))
            expected = row["first8_perl"]
        assert actual == expected, (gate, row["what"], seed, expected, actual)
        counts[gate] += 1
    assert counts == {"A0": 6, "A1": 104, "A2": 54}

    g3dir = base / "round19/G3"
    g3 = module("g3_gen_py27", g3dir / "gen_py27.py")
    v3 = json.loads((g3dir / "validation.json").read_text())
    for seed, row in v3["vectors"]["pinned"].items():
        encoded = seed.encode("latin-1")
        assert g3.py2_str_hash(encoded, 64) == row["py2_hash_64"]
        assert g3.py2_str_hash(encoded, 32) == row["py2_hash_32_gen"]
        for mode, key in (("random29", "py27_random29_first16"),
                          ("grb5_rej", "py27_grb5_rej_first16")):
            assert g3.keystream(seed, mode, 16, wordsize=64) == row[key], (seed, mode)
    test3 = subprocess.run([sys.executable, str(g3dir / "gen_py27.py"), "--selftest"],
                           capture_output=True, text=True, check=True)
    sgdir = base / "round20/S-G3"
    sgtest = subprocess.run([sys.executable, str(sgdir / "test_sg3.py")],
                            capture_output=True, text=True, check=True)
    rows = [json.loads(s) for s in (sgdir / "sweep.jsonl").read_text().splitlines() if s.strip()]
    sg = json.loads((sgdir / "out_sweep.json").read_text())
    sg_summary = sg["summary"]
    sg_rows = rows[1:]
    assert rows[0]["v"] == "SWEEPROW/3"
    assert all("w" in row for row in sg_rows)
    assert len({r["w"] for r in sg_rows}) == len(sg_rows)
    assert len(sg_rows) == sg_summary["survivors_stage_b"] == 230
    assert sum(bool(r["hit"]) for r in sg_rows) == sg_summary["hits"] == 0
    pos = json.loads((sgdir / "out_poscontrol.json").read_text())
    assert pos["PASS"] and pos["rank1_recovery"]["rank"] == 1

    tail = base / "round25/compute-tail"
    progress = json.loads((tail / "progress.json").read_text())
    plant_line = (tail / "chunk1_stdout.json").read_text().splitlines()[0]
    plant = json.loads(plant_line.split(": ", 1)[1])
    assert progress["next_seed"] - progress["tail_start"] == progress["seeds_done"]
    assert plant["hit"] and plant["recovery"] == plant["heldout"] == 1.0
    tex_objects = subprocess.check_output(
        ["git", "-C", str(source), "ls-tree", "-r", "--name-only", "HEAD",
         "liber-primus/analysis/round19/G4/tex"], text=True
    ).splitlines()
    assert not any(re.search(r"/ref_.*\.txt$", x) for x in tex_objects)
    return {
        "schema": "generator-cohort-bounded-receipt-v1",
        "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
        "pinned_input_count": len(hashes),
        "post_plan_dependency_addendum": {"path": extra_path, "sha256": extra_hash,
                                            "bytes": len(extra_raw)},
        "g1": {"model_first12_vectors_matched": count,
               "external_oracle_generators_not_replayed": ["openssl_enc_rc4_k", "shuf_random_source"]},
        "g2": {"model_prefix_rows_matched": counts, "era_perl_runtime_not_replayed": True},
        "g3": {"pinned_seed_count": len(v3["vectors"]["pinned"]),
               "hash_and_stream_assertions": 28, "source_model_selftest": test3.stdout.strip(),
               "actual_cpython27_runtime_not_replayed": True},
        "sg3": {"binding_test": sgtest.stdout.strip(), "saved_sweep_rows": len(sg_rows),
                "saved_summary": sg_summary, "target_sweep_not_replayed": True},
        "r25": {"tail_start": progress["tail_start"], "next_seed": progress["next_seed"],
                "seeds_done_saved": progress["seeds_done"], "best_pmax_saved": progress["best_pmax"],
                "flagged_survivors_saved": progress["flagged_survivors"],
                "saved_plant": plant, "target_chunk_not_replayed": True},
        "g4": {"source_tex_reference_vectors_present": False,
               "tex_source_count": sum(x.endswith(".tex") for x in tex_objects),
               "local_tex_executable": shutil.which("tex"),
               "local_pdftex_executable": shutil.which("pdftex"),
               "actual_tex_runtime_not_replayed": True},
        "interpretation": "Source-model prefixes and saved arithmetic only; no new LP2 search or original-runtime parity."
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        result = run(args.source_root, pathlib.Path(td))
    output = HERE / "receipt.json"
    if args.check:
        assert json.loads(output.read_text(encoding="utf-8")) == result
        print("PASS bounded generator receipt")
    else:
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print("Wrote", output)


if __name__ == "__main__":
    main()
