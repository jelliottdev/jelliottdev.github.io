"""Independent check of the A-03 receipt arithmetic and its logical limit."""
import argparse
import hashlib
import json
import math
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parents[3] / "source-cache" / "dukotah-cicada3301" / "liber-primus"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=pathlib.Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text())
    got = json.loads((HERE / "results.json").read_text())
    for name, digest in plan["input_sha256"].items():
        assert hashlib.sha256((args.source_root / name).read_bytes()).hexdigest() == digest

    report = json.loads((args.source_root / "analysis/round10/L1-template/diff3_report.json").read_text())
    source = json.loads((args.source_root / "analysis/round16/A-03/results.json").read_text())
    notes = (args.source_root / "analysis/round10/L1-template/doublet_final.log").read_text()
    program = (args.source_root / "analysis/round16/A-03/a03_hapl_bound.py").read_text()
    rows = json.loads((args.source_root / "analysis/round10/L1-template/read4.json").read_text())

    assert got["components_loaded"] == len(rows) == 13381
    assert got["agreement_percent"] == report["agreement_exact"] == source["agreement_exact_pct"]
    assert got["agreement_percent"] < got["agreement_gate_percent"] == 99.5
    assert got["agreement_gate_passed"] is False

    def counts(prefix):
        row = next(s for s in notes.splitlines() if prefix in s)
        m = re.search(r"(\d+)\s*/\s*(\d+)", row)
        assert m
        return [int(m[1]), int(m[2])]

    assert got["source_counts"]["image"] == counts("IMAGE-ONLY") == [108, 12484]
    assert got["source_counts"]["canon_per_line"] == counts("CANON per-line") == [82, 12362]
    assert got["source_counts"]["delta_plus_one"] == counts("delta  +1") == [8, 988]
    assert got["source_reported_count_exact"] == {"image": [7, 999], "canon": [7, 999]}
    assert got["observed_surplus"] == 108 - 82 == source["image_canon_surplus_doublets"]
    threshold = math.ceil(12955 * 0.0138) - 86
    assert got["K_needed_at_source_floor"] == threshold == 93
    assert got["source_reported_K_bound"] == source["K_bound"] == 26

    # Independently recompute the simple arithmetic K control at every saved K.
    for label, published_z in got["arithmetic_only_control_z"].items():
        k = int(label)
        img = (108 + k) / (12484 + k)
        canon = 86 / 12955
        variance = img * (1 - img) / (12484 + k) + canon * (1 - canon) / 12955
        assert abs((img - canon) / math.sqrt(variance) - published_z) < 0.000001
    assert got["arithmetic_only_first_K_above_z2"] == source["positive_control_K_min"] == 3
    assert len(re.findall(r"\brecs\b", program)) == 1
    assert got["source_program_uses_component_rows_after_loading"] is False
    assert got["source_program_parses_doublet_log"] is False

    # A possible nonnegative error assignment with 93 hidden events has the same net count.
    witness = got["nonnegative_counterexample_to_K_upper_bound"]
    assert witness["true_merges"] == 93
    assert witness["net_observed_surplus"] == (
        witness["true_merges"] + witness["false_positive_image_doublets"] - witness["missed_image_doublets"]
    ) == 26
    print("Independent source-receipt, gate, and counterexample checks passed")


if __name__ == "__main__":
    main()
