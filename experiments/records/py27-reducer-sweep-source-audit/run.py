"""Audit the pinned R21-L3 receipts and the source's control path.

This deliberately does not claim to rerun the 884,000-word search: its trained
panel and several training corpora are absent from the pinned public tree.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "source"
LANE = ROOT / "liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map"
MISSING_INPUTS = (
    "liber-primus/analysis/round19/I2/models/panel.npz",
    "liber-primus/data/keys/mabinogion.txt",
    "liber-primus/data/kjv.txt",
    "liber-primus/data/keys/welsh/welsh_mabinogion.txt",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_order() -> list[int]:
    prior = json.loads((ROOT / "liber-primus/analysis/round20/P3/seedprior20.json").read_text())
    seen: set[int] = set()
    result: list[int] = []

    def add(w: int) -> None:
        w &= 0xFFFFFFFF
        if w not in seen:
            seen.add(w)
            result.append(w)

    for entry in prior["order"]:
        add(int(entry["seed"]))
    for entry in prior["order"][:64]:
        s = int(entry["seed"])
        for delta in range(-512, 513):
            add(s + delta)
    return result


def calls_in_method(path: Path, function: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    result = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        f = child.func
        if isinstance(f, ast.Name):
            result.append(f.id)
        elif isinstance(f, ast.Attribute):
            result.append(f.attr)
    return result


def calculate() -> dict:
    manifest = json.loads((HERE / "source-manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        assert path.is_file() and sha(path) == entry["sha256"], entry["path"]

    aggregate = json.loads((LANE / "out_reducers.json").read_text(encoding="utf-8"))
    positive = json.loads((LANE / "out_poscontrol.json").read_text(encoding="utf-8"))
    jsonl = [json.loads(s) for s in (LANE / "reducers_sweep.jsonl").read_text().splitlines()]
    header, rows = jsonl[0], jsonl[1:]
    assert header == aggregate["header"]
    prior = prior_order()
    by_config = []
    for saved in aggregate["per_config"]:
        cfg = saved["config"]
        cfg_rows = [r for r in rows if r["config"] == cfg]
        best = max(cfg_rows, key=lambda r: r["pmax"]) if cfg_rows else None
        by_config.append({
            "config": cfg,
            "source_reported_words_screened": saved["words_screened"],
            "verified_survivor_rows": len(cfg_rows),
            "source_reported_survivors": saved["survivors_stage_b"],
            "verified_hit_rows": sum(bool(r["hit"]) for r in cfg_rows),
            "verified_bar_clear_rows": sum(bool(r["clears"]) for r in cfg_rows),
            "best_saved_stage_b_pmax": best["pmax"] if best else None,
            "source_reported_best_stage_b_pmax": saved["top_survivors_by_pmax"][0]["pmax"] if best else None,
            "prior_front_is_within_reported_count": saved["words_screened"] >= len(prior),
        })
    pos_path = LANE / "poscontrol.py"
    sweep_path = LANE / "sweep.py"
    control_calls = calls_in_method(pos_path, "run_config")
    stage_a_calls = calls_in_method(sweep_path, "stage_a")
    sweep_worker_calls = calls_in_method(sweep_path, "worker")
    assert "evaluate" in control_calls
    assert "beam_decode" in stage_a_calls and "stage_a" in sweep_worker_calls
    assert "adjudicate" in stage_a_calls
    verified_rows = len(rows)
    return {
        "source_commit": manifest["commit"],
        "source_manifest_sha256": sha(HERE / "source-manifest.json"),
        "source_reported_words_screened": aggregate["total_words_screened"],
        "source_reported_hit_count": aggregate["total_hits"],
        "verified_saved_survivor_rows": verified_rows,
        "verified_saved_hit_rows": sum(bool(r["hit"]) for r in rows),
        "verified_saved_bar_clear_rows": sum(bool(r["clears"]) for r in rows),
        "verified_saved_recovery_one_rows": sum(r["recovery"] == 1 for r in rows),
        "verified_saved_max_stage_b_pmax": max(r["pmax"] for r in rows),
        "claim_bar_from_saved_header": header["claim_bar_pmax"],
        "source_reported_positive_controls_pass": positive["PASS_all"],
        "source_reported_positive_controls": {r["config"]: r["PASS"] for r in positive["configs"]},
        "prior_source_entries": len(json.loads((ROOT / "liber-primus/analysis/round20/P3/seedprior20.json").read_text())["order"]),
        "unique_prior_front_words": len(prior),
        "prior_front_sha256": hashlib.sha256("".join(f"{w}\n" for w in prior).encode()).hexdigest(),
        "per_config": by_config,
        "gate_audit": {
            "positive_control_calls_full_evaluate": "evaluate" in control_calls,
            "positive_control_calls_stage_a": "stage_a" in control_calls,
            "positive_control_calls_beam_in_full_length_rank_subtest": "beam_decode" in control_calls,
            "actual_sweep_calls_stage_a": "stage_a" in sweep_worker_calls,
            "stage_a_calls_beam_decode_and_adjudicate": "beam_decode" in stage_a_calls and "adjudicate" in stage_a_calls,
            "stage_a_recall_on_plants_verified": False,
        },
        "absent_required_source_inputs": list(MISSING_INPUTS),
        "exact_884000_word_replay_possible_from_bundle": False,
        "interpretation": "Saved Stage-B rows and prior order are auditable; the 884,000 screened-word total remains source-reported. The source positive control bypasses Stage A, so promotion recall is unmeasured. The trained panel and its original training inputs are absent.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    target = HERE / "results.json"
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        assert target.read_text(encoding="utf-8") == payload, "results.json differs"
        print("PASS: source hashes, saved rows, seed front, and gate path")
    else:
        target.write_text(payload, encoding="utf-8", newline="\n")
        print("Wrote", target)


if __name__ == "__main__":
    main()
