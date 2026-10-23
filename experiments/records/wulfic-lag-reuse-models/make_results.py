"""Summarize the two fully verified amended-source replays."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-dir", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = {}
    for stage in ("ac", "ad"):
        receipt_path = args.replay_dir / f"replay_{stage}.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt = receipt.get(stage, receipt)
        if receipt["source_return_code"] != 0:
            raise AssertionError((stage, "source null gate void"))
        source = {}
        for kind in ("lags", "top", "controls"):
            name = f"stage_{stage}_{kind}.tsv"
            generated = args.replay_dir / name
            archived = HERE / f"source-{name}"
            if generated.read_bytes() != archived.read_bytes():
                raise AssertionError((stage, kind, "generated/source rows differ"))
            if sha(archived) != plan["source"][f"published_{stage}_{kind}_sha256"]:
                raise AssertionError((stage, kind, "source hash"))
            source[kind] = read_rows(archived)
        controls = source["controls"]
        top = source["top"]
        lag_rows = source["lags"]
        primary = "periodic" if stage == "ac" else "autokey"
        metric = "P_or_M" if stage == "ac" else "L_or_M"
        by_length = defaultdict(list)
        for row in controls:
            if row["kind"] == primary:
                by_length[int(row[metric])].append(float(row["min"]))
        pmax = 0
        for length in sorted(by_length):
            if min(by_length[length]) <= -10:
                break
            pmax = length
        reuse_lengths = sorted({int(row[metric]) for row in controls if row["kind"] == "reuse"})
        mmin = next((length for length in reuse_lengths if all(
            int(row["at_least_30"]) == int(row["draws"])
            for row in controls if row["kind"] == "reuse" and int(row[metric]) == length)), None)
        if (stage, pmax, mmin) not in (("ac", 12500, 3000), ("ad", 12900, 200)):
            raise AssertionError((stage, pmax, mmin))
        best = {kind: max(float(row["nats"]) for row in top if row["statistic"] == kind)
                for kind in ("F", "S-forward", "S-reverse")}
        if max(best.values()) >= 30:
            raise AssertionError((stage, "source pass appears"))
        exclusion_field = "excluded_of_87" if stage == "ac" else "excluded_of_116"
        result[stage] = {
            "source_return_code": 0,
            "lag_rows": len(lag_rows), "top_rows": len(top), "control_rows": len(controls),
            "pmax": pmax, "mmin": mmin,
            "best": best,
            "excluded_trusted_hypotheses": sum(int(row[exclusion_field]) for row in lag_rows),
            "source_table_sha256": {kind: sha(HERE / f"source-stage_{stage}_{kind}.tsv")
                                    for kind in ("lags", "top", "controls")},
        }
        if stage == "ad":
            leading_F = max((row for row in top if row["statistic"] == "F"),
                            key=lambda row: float(row["nats"]))
            lag = int(leading_F["lag_or_sigma"])
            q = json.loads((HERE / "source-model.json").read_text(encoding="utf-8"))["q"]
            emission_max = max(0.9 * 29 * item + 0.1 for item in q)
            result[stage]["best_F_lag"] = lag
            result[stage]["best_F_pairs"] = 12956 - lag
            result[stage]["best_F_absolute_bound"] = (12956 - lag) * math.log(emission_max)
    (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
