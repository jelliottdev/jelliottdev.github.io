"""Recount source fits and test their observed-size prediction on reserved rows."""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "liber-primus" / "analysis" / "round19" / "I1"
GAMMA = 0.5772156649015329


def block_mean(values: list[float], block: int, reps: int, seed: int) -> float:
    rng = random.Random(seed)
    maxima: list[float] = []
    for _ in range(reps):
        shuffled = values.copy()
        rng.shuffle(shuffled)
        maxima.extend(max(shuffled[start:start + block])
                      for start in range(0, len(shuffled) - block + 1, block))
    return statistics.fmean(maxima)


def independent_fit(scores: list[float]) -> dict:
    n = len(scores)
    b1 = 10 if n < 1000 else 20
    b2 = min(n // 4, 200)
    m1, m2 = block_mean(scores, b1, 40, 11), block_mean(scores, b2, 40, 11)
    beta = (m2 - m1) / math.log(b2 / b1)
    mu = m1 - beta * (math.log(b1) + GAMMA)
    sd = statistics.pstdev(scores)
    return {"b1": b1, "b2": b2, "m_b1": m1, "m_b2": m2,
            "mu": mu, "beta": beta, "bulk_mean": statistics.fmean(scores),
            "bulk_sd": sd, "beta_from_bulk_sd": sd * math.sqrt(6) / math.pi,
            "observed_max": max(scores), "n": n}


def verify_math() -> None:
    for mu, beta, n, alpha in ((-6.5, .08, 10**6, .01), (-5.7, .12, 10**9, .01)):
        bar = mu + beta * (math.log(n) - math.log(-math.log1p(-alpha)))
        tail = -math.expm1(-n * math.exp(-(bar - mu) / beta))
        assert abs(tail - alpha) < 1e-12


def main(capture: bool = False) -> dict:
    verify_math()
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    file_counts = {}
    for name in ("out_fp_deep.json", "out_fp_deep2.json", "out_fp_curve.json"):
        rows = json.loads((SOURCE / name).read_text(encoding="utf-8"))["rows"]
        file_counts[name] = len(rows)
        for row in rows:
            grouped[(row["null"], row["mode"])].append(row)
    assert file_counts == {"out_fp_deep.json": 20000, "out_fp_deep2.json": 8000,
                           "out_fp_curve.json": 6000}
    archived = json.loads((SOURCE / "out_fp_tail.json").read_text(encoding="utf-8"))["fits"]
    assert len(grouped) == len(archived) == 26
    by_key = {(row["null"], row["mode"]): row for row in archived}
    diagnostic = []
    for key in sorted(grouped):
        rows = grouped[key]
        scores = [row["score"] for row in rows]
        f = independent_fit(scores)
        old = by_key[key]
        for field, value in f.items():
            assert math.isclose(value, old[field], abs_tol=1e-10, rel_tol=0), (key, field)
        extra = {
            "mean_n_skips": statistics.fmean(row["n_skips"] for row in rows),
            "E_max_1e6": f["mu"] + f["beta"] * (math.log(10**6) + GAMMA),
            "E_max_1e9": f["mu"] + f["beta"] * (math.log(10**9) + GAMMA),
            "fw_bar_1e6": f["mu"] + f["beta"] * (math.log(10**6) - math.log(-math.log1p(-.01))),
            "fw_bar_1e9": f["mu"] + f["beta"] * (math.log(10**9) - math.log(-math.log1p(-.01))),
        }
        for field, value in extra.items():
            assert math.isclose(value, old[field], abs_tol=1e-10, rel_tol=0), (key, field)
        train, heldout = scores[::2], scores[1::2]
        trained = independent_fit(train)
        probes = []
        for b in (10, 25, 50):
            measured = block_mean(heldout, b, 80, 20261023 + b)
            predicted = trained["mu"] + trained["beta"] * (math.log(b) + GAMMA)
            probes.append({"block_size": b, "predicted": predicted,
                           "heldout_mean_max": measured, "difference": measured - predicted})
        diagnostic.append({"null": key[0], "mode": key[1], "train_rows": len(train),
                           "heldout_rows": len(heldout), "probes": probes})
    summary = {str(b): statistics.median(abs(row["difference"])
                   for cell in diagnostic for row in cell["probes"] if row["block_size"] == b)
               for b in (10, 25, 50)}
    report = {"schema": "round19-i1-tail-independent-check-v1", "input_rows": 34000,
              "source_fit_cells": 26, "all_source_fit_fields_match": True,
              "heldout_split": "even ordinal training, odd ordinal held out within each null/mode cell",
              "heldout_median_abs_error_by_block": summary, "diagnostic": diagnostic}
    target = HERE / "results.json"
    if capture:
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    else:
        assert json.loads(target.read_text(encoding="utf-8")) == report
    print(json.dumps({k: report[k] for k in ("input_rows", "source_fit_cells",
                                            "all_source_fit_fields_match", "heldout_median_abs_error_by_block")},
                     indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    main(parser.parse_args().capture)
