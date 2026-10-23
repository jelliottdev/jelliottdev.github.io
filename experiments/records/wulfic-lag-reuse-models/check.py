"""Independently check archived AC/AD tables against site runes and pair laws."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
N = 29
MIN_SEPARATION = 11
SAMPLE_LAGS = (11, 100, 1033, 3301, 9000, 12500, 12900, 12945)


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def site_stream():
    alphabet = {item["rune"]: item["index"] for item in json.loads(
        (ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    return bytes(alphabet[rune] for i in range(56)
                 for rune in json.loads((ROOT / f"data/pages/lp2-{i:02d}.json").read_text(encoding="utf-8"))["raw"]
                 if rune in alphabet)


def score_tables(q, stage):
    x = np.arange(N)
    if stage == "ac":
        difference = np.asarray([sum(q[p] * q[(p+d) % N] for p in range(N)) for d in range(N)])
        summed = np.asarray([sum(q[p] * q[(d-p) % N] for p in range(N)) for d in range(N)])
        return np.asarray([
            [np.log(N * difference[(x-a) % N]) for a in range(N)],
            [np.log(N * summed[(x-a) % N]) for a in range(N)],
            [np.log(N * summed[(a-x) % N]) for a in range(N)],
        ]), ("diff", "sum", "sumrev")
    emission = np.log((1 - 0.1) * N * q + 0.1)
    forward = np.asarray([emission[(x-a) % N] for a in range(N)])
    reversed_ = np.asarray([emission[(a-x) % N] for a in range(N)])
    return np.asarray([forward, reversed_, forward, reversed_]), ("diff", "diffrev", "sum", "sumrev")


def combine(ci, cj, stage):
    diff = (cj-ci) % N
    summed = (cj+ci) % N
    return (diff, summed, summed) if stage == "ac" else (diff, diff, summed, summed)


def stat(table, observed):
    scores = table[:, observed]
    cumulative = np.concatenate((np.zeros((table.shape[0], 1)), np.cumsum(scores, axis=1)), axis=1)
    forward = cumulative[:, -1]
    strongest = (cumulative - np.minimum.accumulate(cumulative, axis=1)).max(axis=1)
    return forward, strongest


def forward_lag(cipher, table, stage, lag):
    components = combine(cipher[:-lag], cipher[lag:], stage)
    stats = [stat(table[r], value) for r, value in enumerate(components)]
    return np.asarray([part[0] for part in stats]), np.asarray([part[1] for part in stats])


def reverse_score(cipher, table, stage, sigma, relation, shift):
    start = max(0, sigma - len(cipher) + 1)
    stop = (sigma - MIN_SEPARATION) // 2 + 1
    ii = np.arange(start, stop)
    jj = sigma - ii
    x = combine(cipher[ii], cipher[jj], stage)[relation]
    return float(stat(table[relation, shift:shift+1], x)[1][0])


def verify():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    source = plan["source"]
    cipher_bytes = (HERE / "source-stream.bin").read_bytes()
    if cipher_bytes != site_stream() or len(cipher_bytes) != 12956:
        raise AssertionError("Source GP29 stream differs from site pages")
    cipher = np.frombuffer(cipher_bytes, dtype=np.uint8).astype(np.int64)
    model = json.loads((HERE / "source-model.json").read_text(encoding="utf-8"))
    q = np.asarray(model["q"], dtype=np.float64)
    if model["source_commit"] != source["commit"] or len(q) != N or abs(q.sum()-1) > 1e-12:
        raise AssertionError("Invalid solved-LP1 model")
    out = {}
    for stage in ("ac", "ad"):
        lag_file = HERE / f"source-stage_{stage}_lags.tsv"
        top_file = HERE / f"source-stage_{stage}_top.tsv"
        controls_file = HERE / f"source-stage_{stage}_controls.tsv"
        for kind, path in (("lags", lag_file), ("top", top_file), ("controls", controls_file)):
            if sha(path) != source[f"published_{stage}_{kind}_sha256"]:
                raise AssertionError(f"Pinned {stage} {kind} table hash differs")
        lag_rows, top_rows, controls = rows(lag_file), rows(top_file), rows(controls_file)
        if len(lag_rows) != 12935 or len(top_rows) != 60 or len(controls) != (138 if stage == "ac" else 184):
            raise AssertionError((stage, "row counts", len(lag_rows), len(top_rows), len(controls)))
        table, names = score_tables(q, stage)
        pmax = 12500 if stage == "ac" else 12900
        exclusion_field = "excluded_of_87" if stage == "ac" else "excluded_of_116"
        sampled = 0
        for lag in SAMPLE_LAGS:
            row = lag_rows[lag - MIN_SEPARATION]
            if int(row["lag"]) != lag or int(row["pairs"]) != len(cipher)-lag:
                raise AssertionError((stage, lag, "lag metadata"))
            F, S = forward_lag(cipher, table, stage, lag)
            winner = np.unravel_index(np.argmax(F), F.shape)
            expected = (f"{F[0,0]:.2f}", f"{F.max():.2f}", names[winner[0]], str(winner[1]),
                        str(int(np.count_nonzero(F <= -10)) if lag <= pmax else 0), f"{S.max():.2f}")
            actual = (row["F_diff0"], row["F_best"], row["best_rel"], row["best_a"],
                      row[exclusion_field], row["S_fwd_best"])
            if expected != actual:
                raise AssertionError((stage, lag, "independent forward check", expected, actual))
            sampled += 1
        # Each source top table retains 20 full F, 20 forward-stretch and 20
        # reverse-stretch maxima. Check one leading cell from each statistic.
        for kind in ("F", "S-forward", "S-reverse"):
            entry = next(row for row in top_rows if row["statistic"] == kind)
            position, relation, shift = int(entry["lag_or_sigma"]), names.index(entry["relation"]), int(entry["a"])
            if kind == "S-reverse":
                value = reverse_score(cipher, table, stage, position, relation, shift)
            else:
                F, S = forward_lag(cipher, table, stage, position)
                value = float((F if kind == "F" else S)[relation, shift])
            if f"{value:.2f}" != entry["nats"]:
                raise AssertionError((stage, kind, value, entry["nats"]))
        result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))[stage]
        if result["source_return_code"] != 0 or result["pmax"] != pmax:
            raise AssertionError((stage, "source validity and calibrated range"))
        if result["lag_rows"] != len(lag_rows) or result["control_rows"] != len(controls):
            raise AssertionError((stage, "summary row counts"))
        if stage == "ad":
            top_whole = max((row for row in top_rows if row["statistic"] == "F"),
                            key=lambda row: float(row["nats"]))
            lag = int(top_whole["lag_or_sigma"])
            maximum = (len(cipher)-lag) * math.log(max(0.9 * N * q + 0.1))
            if result["best_F_lag"] != lag or result["best_F_pairs"] != len(cipher)-lag:
                raise AssertionError("Best AD whole-lag opportunity count changed")
            if abs(result["best_F_absolute_bound"] - maximum) > 1e-12 or maximum >= 30:
                raise AssertionError("Best AD whole-lag pass-impossibility bound changed")
        out[stage] = {"forward_rows_recomputed": sampled, "top_cells_recomputed": 3,
                      "lag_rows_hashed": len(lag_rows), "control_rows_hashed": len(controls)}
    print("PASS: site/source 12,956 runes and independent AC/AD sampled F/S cells; six full source-table digests")
    return out


if __name__ == "__main__":
    verify()
