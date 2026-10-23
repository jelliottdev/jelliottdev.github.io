"""Replay the pinned ten-page literal-F mask grid and source second layer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from engine import mask_positions, parse_page, scan_masks, source_weights
from gate import load_source
from snapshot_inputs import HERE, git_bytes


def digest(values: list[int]) -> str:
    return hashlib.sha256(bytes(values)).hexdigest()


def source_receipt(source_root: Path, pin: dict) -> dict:
    source = git_bytes(source_root, pin["script_path"])
    with tempfile.TemporaryDirectory() as temp:
        tools = Path(temp) / "tools"
        (tools / "legacy").mkdir(parents=True)
        script = tools / "legacy" / "p21_30_second_layer.py"
        script.write_bytes(source)
        for page in pin["pages"]:
            folder = tools / "pages" / f"page_{page['source_page']:02d}"
            folder.mkdir(parents=True)
            raw = page["raw"].encode("utf8")
            assert hashlib.sha256(raw).hexdigest() == page["source_sha256"]
            (folder / "runes.txt").write_bytes(raw)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        p = subprocess.run(["python", str(script)], cwd=temp, env=env, capture_output=True,
                           encoding="utf8", timeout=180, check=True)
        stdout = p.stdout.replace("\r\n", "\n")
    rows = []
    for page in pin["pages"]:
        old = page["source_page"]
        match = re.search(rf"^PAGE {old}: .*?(?=^PAGE {old+1}: |^ANALYSIS COMPLETE|\Z)", stdout, re.M | re.S)
        assert match, old
        block = match.group()
        baseline = re.search(r"\[No F-skip\] IoC=([0-9.]+) \| Singles: (\d+)/(\d+)", block)
        assert baseline
        success = re.search(r"\[Best F-skip \(all singles pass\)\] IoC=([0-9.]+) bg=(\d+) score=([0-9.]+).*?F-skip at: \[([^\]]*)\]", block, re.S)
        fallback = re.search(r"\[Best IoC F-skip\] IoC=([0-9.]+) \(mask: \[([^\]]*)\]\)", block)
        status = "all-singleton" if success else "best-ioc-fallback" if fallback else "no-improvement"
        raw_positions = success.group(4) if success else fallback.group(2) if fallback else ""
        mask = [int(v.strip()) for v in raw_positions.split(",") if v.strip()]
        rows.append({"source_page": old, "status": status, "baseline_ioc_printed": float(baseline.group(1)),
                     "baseline_singletons_printed": [int(baseline.group(2)), int(baseline.group(3))],
                     "chosen_mask_printed": mask,
                     "selected_ioc_printed": float(success.group(1)) if success else float(fallback.group(1)) if fallback else None,
                     "selected_bigram_printed": int(success.group(2)) if success else None,
                     "selected_score_printed": float(success.group(3)) if success else None})
    return {"schema": "wulfic-p21-source-receipt-v1", "source_stdout_sha256": hashlib.sha256(stdout.encode("utf8")).hexdigest(),
            "source_stdout_bytes": len(stdout.encode("utf8")), "pages": rows}


def second_layer(source: dict, values: list[int]) -> dict:
    n = len(values)
    baseline_bg = source["score_text"](values)
    rows = []
    for name, out in source["rearrange_by_primes"](values, n).items():
        rows.append((name, out, len(out) > 5 and source["ioc"](out) > 1.3))
    for width in [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]:
        for label, fn in (("column", source["columnar_transposition"]),
                          ("reverse_column", source["reverse_columnar"]),
                          ("spiral", source["spiral_read"])):
            out = fn(values, width)
            printed = source["ioc"](out) > 1.5 and source["score_text"](out) > baseline_bg * 1.2
            rows.append((f"{label}_{width}", out, printed))
    return {"route_count": len(rows), "printed_count": sum(bool(r[2]) for r in rows),
            "routes": [{"name": name, "length": len(out), "ioc": source["ioc"](out),
                        "bigram": source["score_text"](out), "printed": bool(printed), "sha256": digest(out)}
                       for name, out, printed in rows]}


def scan_page(page: dict, source: dict, weights: np.ndarray, values: np.ndarray | None = None,
              include_second_layer: bool = False) -> dict:
    parsed, singletons, words = parse_page(page["raw"])
    if values is None:
        values = parsed
    key_name, mode_name = source["PAGE_KEYS"][page["source_page"]]
    key = source["parse_keyword"](key_name)
    assert key
    mode = {"sub": 0, "add": 1, "beaufort": 2}[mode_name]
    scan = scan_masks(values, np.array(key, dtype=np.int16), mode, singletons, weights)
    (f_count, n_single, gated, baseline_ioc, baseline_bg, best_score,
     best_score_mask, best_score_ioc, best_score_bg, best_ioc, best_ioc_mask) = scan
    result = {"source_page": page["source_page"], "current_page": page["current_page"],
              "keyword": key_name, "parsed_key": key, "mode": mode_name, "runes": len(values),
              "cipher_F_count": int(f_count), "mask_count": 1 << f_count,
              "singleton_count": int(n_single), "all_singleton_masks": int(gated),
              "baseline_ioc": float(baseline_ioc), "baseline_bigram": int(baseline_bg),
              "best_gated_score": float(best_score) if gated else None,
              "best_gated_ioc": float(best_score_ioc) if gated else None,
              "best_gated_bigram": int(best_score_bg) if gated else None,
              "best_gated_mask": mask_positions(values, int(best_score_mask)) if gated else None,
              "best_ioc": float(best_ioc), "best_ioc_mask": mask_positions(values, int(best_ioc_mask))}
    if include_second_layer:
        plain = source["decrypt_vigenere"](list(values), key, mode_name)
        assert abs(source["ioc"](plain) - baseline_ioc) < 1e-12
        result["standard_decode_sha256"] = digest(plain)
        result["second_layer"] = second_layer(source, plain)
        result["word_order_views"] = {"prime_0idx": True, "prime_1idx": True,
                                       "reverse": True, "magic_first25": len(words) >= 25}
    return result


def build(source_root: Path) -> tuple[dict, dict]:
    pin = json.loads((HERE / "inputs.json").read_text(encoding="utf8"))
    gate = json.loads((HERE / "gate.json").read_text(encoding="utf8"))
    assert gate["planted_full_recovery"] and gate["compiled_full_mask_plant_parity"]
    source_bytes = git_bytes(source_root, pin["script_path"])
    assert hashlib.sha256(source_bytes).hexdigest() == pin["script_sha256"]
    source = load_source(source_root)
    weights = source_weights(source_bytes)
    actual = [scan_page(p, source, weights, include_second_layer=True) for p in pin["pages"]]
    receipt = source_receipt(source_root, pin)
    for ours, theirs in zip(actual, receipt["pages"]):
        assert ours["source_page"] == theirs["source_page"]
        assert abs(ours["baseline_ioc"] - theirs["baseline_ioc_printed"]) < .00006
        if ours["all_singleton_masks"]:
            assert theirs["status"] == "all-singleton"
            assert ours["best_gated_mask"] == theirs["chosen_mask_printed"]
            assert abs(ours["best_gated_ioc"] - theirs["selected_ioc_printed"]) < .00006
            assert ours["best_gated_bigram"] == theirs["selected_bigram_printed"]
        else:
            expected_mask = ours["best_ioc_mask"] if ours["best_ioc"] > ours["baseline_ioc"] + 1e-12 else []
            assert theirs["chosen_mask_printed"] == expected_mask
    rng = np.random.default_rng(20261023)
    controls = []
    for rep in range(19):
        rows = []
        for page in pin["pages"]:
            original, _, _ = parse_page(page["raw"])
            shuffled = rng.permutation(original)
            rows.append(scan_page(page, source, weights, shuffled))
        scores = [r["best_gated_score"] for r in rows if r["all_singleton_masks"]]
        controls.append({"replicate": rep, "gated_page_count": len(scores),
                         "best_gated_score": max(scores) if scores else None,
                         "per_page": [{"current_page": r["current_page"], "all_singleton_masks": r["all_singleton_masks"],
                                       "best_gated_score": r["best_gated_score"]} for r in rows]})
    actual_scores = [r["best_gated_score"] for r in actual if r["all_singleton_masks"]]
    best_actual = max(actual_scores) if actual_scores else None
    summary = {"schema": "wulfic-p21-literal-f-results-v1",
               "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
               "inputs_sha256": hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest(),
               "gate_sha256": hashlib.sha256((HERE / "gate.json").read_bytes()).hexdigest(),
               "observed": {"pages": actual, "total_masks": sum(r["mask_count"] for r in actual),
                            "gated_page_count": len(actual_scores), "best_gated_score": best_actual},
               "controls": {"seed": 20261023, "replicates": 19, "rows": controls,
                            "gated_page_count_exceedances": sum(c["gated_page_count"] >= len(actual_scores) for c in controls),
                            "best_gated_score_exceedances": sum(c["best_gated_score"] is not None and best_actual is not None and c["best_gated_score"] >= best_actual for c in controls)}}
    return summary, receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary, receipt = build(args.source_root)
    for name, value in (("results.json", summary), ("source-run.json", receipt)):
        raw = json.dumps(value, ensure_ascii=False, indent=2).encode("utf8") + b"\n"
        path = HERE / name
        if args.check:
            assert path.read_bytes() == raw, name
        else:
            path.write_bytes(raw)
    print(f"{summary['observed']['total_masks']:,} source masks over ten pages; "
          f"{summary['observed']['gated_page_count']} pages with singleton-valid masks.")


if __name__ == "__main__":
    main()
