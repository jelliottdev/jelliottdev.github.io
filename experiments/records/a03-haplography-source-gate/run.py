"""Audit Round16 A-03 arithmetic and gates against pinned source receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parents[3] / "source-cache" / "dukotah-cicada3301" / "liber-primus"


def build(source: pathlib.Path) -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for relative, expected in plan["input_sha256"].items():
        actual = hashlib.sha256((source / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"pinned input differs: {relative}: {actual}")

    a03 = json.loads((source / "analysis/round16/A-03/results.json").read_text())
    diff = json.loads((source / "analysis/round10/L1-template/diff3_report.json").read_text())
    components = json.loads((source / "analysis/round10/L1-template/read4.json").read_text())
    log = (source / "analysis/round10/L1-template/doublet_final.log").read_text()
    program = (source / "analysis/round16/A-03/a03_hapl_bound.py").read_text()

    def line(pattern: str) -> tuple[int, int]:
        match = re.search(pattern, log)
        if match is None:
            raise ValueError(f"missing source count: {pattern}")
        return int(match.group(1)), int(match.group(2))

    image = line(r"IMAGE-ONLY[^\n]*?:\s*(\d+)\s*/\s*(\d+)")
    canon = line(r"CANON per-line[^\n]*?:\s*(\d+)\s*/\s*(\d+)")
    delta_one = line(r"delta\s+\+1[^\n]*?image doublets\s+(\d+)\s*/\s*(\d+)")
    expected_image = (plan["fixed_rules"]["source_image_doublets"], a03["image_pairs_all"])
    if image != expected_image or canon != (82, 12362) or delta_one != (8, 988):
        raise ValueError("source log and saved result differ")

    gate = plan["fixed_rules"]["agreement_gate_percent"]
    agreement = float(diff["agreement_exact"])
    if abs(agreement - float(a03["agreement_exact_pct"])) > 1e-9:
        raise ValueError("source agreement does not match receipt")
    floor = plan["fixed_rules"]["source_autokey_floor_percent"] / 100
    needed = math.ceil(floor * a03["canon_pairs_continuous"]) - a03["canon_doublets_continuous"]
    surplus = image[0] - canon[0]
    if needed != a03["K_needed_for_autokey"] or surplus != a03["K_bound"]:
        raise ValueError("source arithmetic does not match receipt")

    # Source's 'planted' control changes only an arithmetic K, not any image row.
    k_z = {}
    for k in (0, 1, 3, 5, 10, 20, 50, 93):
        r_i = (image[0] + k) / (image[1] + k)
        r_c = a03["canon_doublets_continuous"] / a03["canon_pairs_continuous"]
        se = math.sqrt(r_i * (1 - r_i) / (image[1] + k) + r_c * (1 - r_c) / a03["canon_pairs_continuous"])
        k_z[str(k)] = round((r_i - r_c) / se, 6)
    first_over_two = next(k for k in range(200) if (
        lambda ri, rc: (ri-rc) / math.sqrt(ri*(1-ri)/(image[1]+k)+rc*(1-rc)/a03["canon_pairs_continuous"])
    )((image[0]+k)/(image[1]+k), a03["canon_doublets_continuous"]/a03["canon_pairs_continuous"]) > 2)

    # There is no observation-only upper bound: missed true doubles and false positives
    # can cancel. This finite nonnegative construction yields the same observed surplus.
    counterexample = {
        "true_merges": needed,
        "false_positive_image_doublets": surplus,
        "missed_image_doublets": needed,
        "net_observed_surplus": needed + surplus - needed,
    }
    assert counterexample["net_observed_surplus"] == surplus
    return {
        "schema": "liberpedia-a03-gate-audit-v1",
        "source_id": "A-03",
        "source_revision": plan["revision"],
        "components_loaded": len(components),
        "agreement_percent": agreement,
        "agreement_gate_percent": gate,
        "agreement_gate_passed": agreement >= gate,
        "source_counts": {"image": list(image), "canon_per_line": list(canon), "delta_plus_one": list(delta_one)},
        "source_reported_count_exact": {"image": [a03["image_doublets_count_exact"], a03["image_pairs_count_exact"]], "canon": [a03["canon_doublets_count_exact"], a03["canon_pairs_count_exact"]]},
        "source_reported_K_bound": a03["K_bound"],
        "observed_surplus": surplus,
        "K_needed_at_source_floor": needed,
        "arithmetic_only_control_z": k_z,
        "arithmetic_only_first_K_above_z2": first_over_two,
        "source_control_first_K": a03["positive_control_K_min"],
        "source_program_uses_component_rows_after_loading": len(re.findall(r"\brecs\b", program)) > 1,
        "source_program_parses_doublet_log": "open(os.path.join(L1, 'doublet_final.log'))" in program,
        "nonnegative_counterexample_to_K_upper_bound": counterexample,
        "finding": "The source's agreement gate fails; its planted-K control is arithmetic only; the observed surplus cannot upper-bound missed merges without a measured classifier error model.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, default=DEFAULT_SOURCE)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    result = build(args.source_root)
    target = HERE / "results.json"
    if args.check:
        if result != json.loads(target.read_text(encoding="utf-8")):
            raise SystemExit("result differs")
    else:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("A-03 receipt and gate audit passed")


if __name__ == "__main__":
    main()
