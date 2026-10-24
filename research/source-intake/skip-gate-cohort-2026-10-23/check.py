"""Independent checks for the finite source-control subset in this intake cohort."""
import argparse
import hashlib
import json
import math
import pathlib
import statistics


HERE = pathlib.Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(source_root):
    plan = load(HERE / "plan.json")
    assert sha((HERE / "plan.json").read_bytes()) == "0de7db384e3e45f636c305bd9f54980f2ab11ade5b119c25e6f1e3e6a92051cd"
    for path, expected in plan["source_sha256"].items():
        assert sha((source_root / path).read_bytes()) == expected, path

    cpath = "liber-primus/analysis/round24/C2-ext-skip-generators/control_ext.json"
    controls = load(HERE / "fresh-control-ext.json")
    assert controls == load(source_root / cpath)
    assert controls["n_seeds"] == 7
    assert len(controls["axes"]) == 8
    for axis, result in controls["axes"].items():
        rows = result["rows"]
        assert len(rows) == 7, axis
        d = statistics.median(r["dec_rec"] for r in rows)
        b = statistics.median(r["beam_rec"] for r in rows)
        assert math.isclose(d, result["dec_median_rec"], abs_tol=1e-12)
        assert math.isclose(b, result["beam_median_rec"], abs_tol=1e-12)
        assert result["control_validated"] == (d >= 0.9 and b < 0.9)
    assert controls["all_validated"] is True

    p3 = "liber-primus/analysis/round20/P3/"
    prior = load(HERE / "fresh-seedprior20.json")
    archived_prior = load(source_root / (p3 + "seedprior20.json"))
    for obj in (prior, archived_prior):
        obj.pop("generated")
        obj["source"] = obj["source"].replace("\\", "/")
    assert prior == archived_prior
    order = prior["order"]
    assert len(order) == prior["candidate_count"] == 433
    assert [row["rank"] for row in order] == list(range(1, 434))
    assert len({row["seed"] for row in order}) == 433
    assert order[0]["seed"] == prior["top_seed"] == 1325734783
    assert all(row["tier_weight"] == {"A": 8.0, "B": 4.0, "C": 2.0, "D": 1.0}[row["tier"]] for row in order)
    bars = load(HERE / "fresh-panelmax20.json")
    archived_bars = load(source_root / (p3 + "panelmax20.json"))
    for obj in (bars, archived_bars):
        obj.pop("generated")
    assert bars == archived_bars
    assert bars["presets"]["exact"]["status"] == "CALIBRATED"
    assert all(bars["presets"][key]["status"] == "PROVISIONAL" for key in ("pair", "exact_ms8", "drift"))

    print("PASS: pinned source hashes; 8/8 seven-seed plant axes and medians; P3 seed-prior and panel-bar fields match archived source, excluding timestamps/path separators")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=pathlib.Path)
    main(ap.parse_args().source_root)
