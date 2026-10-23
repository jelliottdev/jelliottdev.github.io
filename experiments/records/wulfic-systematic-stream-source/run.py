"""Replay the two executable finite branches of pinned stream_cipher_attack.py."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from engine import GOOD_MASK, GRID_SIZE, MODES, decode, lfsr_grid, lfsr_key, score, singleton_positions, stream, stream_names, tuple_from_index

HERE = Path(__file__).resolve().parent
SEED = 20261023
NULLS = 19


def page_arrays(page: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(page["values"], dtype=np.int16)
    singles = singleton_positions(page["word_lengths"])
    assert sum(page["word_lengths"]) == len(values)
    flags = np.zeros(len(values), dtype=np.uint8)
    flags[singles] = 1
    return values, singles, flags


def digest(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype=np.uint8).tobytes()).hexdigest()


def stream_scan(pages: list[dict], detailed: bool) -> dict:
    count = 0; hit_count = 0; best_score = (-float("inf"), None)
    best_ioc = (-float("inf"), None)
    rows = []
    for page in pages:
        values, singles, _ = page_arrays(page)
        page_hit = 0; page_best = (-float("inf"), None)
        for name in stream_names():
            key = stream(name, len(values))
            for mode in MODES:
                metric = score(values, key, singles, mode)
                count += 1
                hit = metric["combined"] > 2.0 or metric["ioc"] > 1.5
                page_hit += int(hit)
                hit_count += int(hit)
                item = {"page": page["page"], "source_ordinal": page["source_ordinal"],
                        "stream": name, "mode": mode, **metric}
                if metric["combined"] > best_score[0]:
                    best_score = (metric["combined"], item)
                if metric["ioc"] > best_ioc[0]:
                    best_ioc = (metric["ioc"], item)
                if metric["combined"] > page_best[0]:
                    page_best = (metric["combined"], item)
        if detailed:
            winner = dict(page_best[1])
            winner["decode_sha256"] = digest(decode(values, stream(winner["stream"], len(values)), winner["mode"]))
            winner["source_hit"] = winner["combined"] > 2.0 or winner["ioc"] > 1.5
            rows.append({"page": page["page"], "source_ordinal": page["source_ordinal"],
                         "tested_settings": len(stream_names()) * len(MODES), "source_hits": page_hit,
                         "best": winner})
    assert count == len(pages) * 26 * 3
    return {"settings": count, "source_hits": hit_count,
            "max_combined": best_score[0], "max_combined_setting": best_score[1] if detailed else None,
            "max_ioc": best_ioc[0], "max_ioc_setting": best_ioc[1] if detailed else None,
            "pages": rows if detailed else None}


def lfsr_scan(pages: list[dict], detailed: bool) -> dict:
    rows = []; max_score = -float("inf"); total_hits = 0
    global_winner = None
    for page in pages:
        values, singles, flags = page_arrays(page)
        scores, hits = lfsr_grid(values, flags, GOOD_MASK)
        page_hits = int(hits.sum())
        total_hits += page_hits
        flat = scores.ravel()
        best_index = int(np.argmax(flat))
        best_score = float(flat[best_index])
        if best_score > max_score:
            max_score = best_score
            global_winner = (page, best_index)
        if detailed:
            # Stable sorting reproduces source tuple/mode iteration ties.
            indices = np.argsort(-flat, kind="stable")[:10]
            top = []
            for row_index in indices:
                config = int(row_index) // 3
                mode = MODES[int(row_index) % 3]
                params = tuple_from_index(config)
                key = lfsr_key(params, len(values))
                exact = score(values, key, singles, mode)
                assert abs(exact["combined"] - flat[row_index]) < 1e-12
                top.append({"state": list(params[:2]), "taps": list(params[2:]),
                            "mode": mode, **exact,
                            "decode_sha256": digest(decode(values, key, mode))})
            rows.append({"page": page["page"], "source_ordinal": page["source_ordinal"],
                         "singleton_count": len(singles), "runes": len(values),
                         "tested_settings": GRID_SIZE * 3, "source_hits": page_hits, "top_10": top})
    assert global_winner is not None
    winning_page, winning_index = global_winner
    return {"settings": len(pages) * GRID_SIZE * 3, "source_hits": total_hits,
            "max_combined": max_score,
            "max_page": winning_page["page"] if detailed else None,
            "max_config_index": winning_index if detailed else None,
            "pages": rows if detailed else None}


def build() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
    assert plan["id"] == HERE.name
    assert json.loads((HERE / "gate.json").read_text(encoding="utf8"))["planted_source_screen"]
    input_raw = (HERE / "inputs.json").read_bytes()
    inputs = json.loads(input_raw)
    pages = inputs["pages"]
    assert len(pages) == 38 and [p["page"] for p in pages] == [f"lp2-{i:02d}" for i in range(1, 39)]
    selected = sorted(pages, key=lambda p: -len(singleton_positions(p["word_lengths"])))[:3]
    assert [(p["page"], len(singleton_positions(p["word_lengths"]))) for p in selected] == [
        ("lp2-28", 12), ("lp2-10", 11), ("lp2-17", 10)]
    observed_stream = stream_scan(pages, True)
    observed_lfsr = lfsr_scan(selected, True)
    rng = np.random.default_rng(SEED)
    control_rows = []
    for rep in range(NULLS):
        permuted = [{**p, "values": rng.permutation(np.asarray(p["values"], dtype=np.int16)).tolist()} for p in pages]
        control_selected = [permuted[p["source_ordinal"] - 18] for p in selected]
        ss = stream_scan(permuted, False)
        ls = lfsr_scan(control_selected, False)
        control_rows.append({"replicate": rep, "stream_source_hits": ss["source_hits"],
                             "stream_max_combined": ss["max_combined"], "stream_max_ioc": ss["max_ioc"],
                             "lfsr_source_hits": ls["source_hits"], "lfsr_max_combined": ls["max_combined"]})
    return {"schema": "wulfic-systematic-stream-results-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "inputs_sha256": hashlib.sha256(input_raw).hexdigest(),
            "gate_sha256": hashlib.sha256((HERE / "gate.json").read_bytes()).hexdigest(),
            "source_commit": inputs["source_commit"],
            "target_pages": [p["page"] for p in pages],
            "lfsr_selected_pages": [p["page"] for p in selected],
            "observed": {"streams": observed_stream, "lfsr": observed_lfsr},
            "controls": {"seed": SEED, "replicates": NULLS, "rows": control_rows,
                         "stream_max_combined_exceedances": sum(r["stream_max_combined"] >= observed_stream["max_combined"] for r in control_rows),
                         "stream_max_ioc_exceedances": sum(r["stream_max_ioc"] >= observed_stream["max_ioc"] for r in control_rows),
                         "lfsr_max_combined_exceedances": sum(r["lfsr_max_combined"] >= observed_lfsr["max_combined"] for r in control_rows)}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    raw = json.dumps(result, ensure_ascii=False, indent=2).encode("utf8") + b"\n"
    target = HERE / "results.json"
    if args.check:
        assert target.read_bytes() == raw
    else:
        target.write_bytes(raw)
    streams = result["observed"]["streams"]
    lfsr = result["observed"]["lfsr"]
    print(f"Streams {streams['settings']} settings, {streams['source_hits']} source hits; LFSR {lfsr['settings']} settings, {lfsr['source_hits']} source hits.")
    print(f"Control exceedances (19): stream combined {result['controls']['stream_max_combined_exceedances']}, stream IoC {result['controls']['stream_max_ioc_exceedances']}, LFSR combined {result['controls']['lfsr_max_combined_exceedances']}.")


if __name__ == "__main__":
    main()
