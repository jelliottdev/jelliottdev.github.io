"""Independent arithmetic check of menu size and exact conditioned null tail."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "sources" / "emmanuel-p20-lf"


def independent_tail(histogram: dict[str, int], draws: int):
    buckets = {int(weight): count for weight, count in histogram.items()}
    assert sum(buckets.values()) == 83 ** 2
    ways = {(0, 0): 1}
    for weight, population in sorted(buckets.items()):
        following = defaultdict(int)
        for (selected, total), multiplicity in ways.items():
            for count in range(min(draws - selected, population) + 1):
                following[(selected + count, total + weight * count)] += multiplicity * math.comb(population, count)
        ways = following
    denominator = math.comb(83 ** 2, draws)
    assert sum(multiplicity for (selected, _), multiplicity in ways.items() if selected == draws) == denominator
    numerator = sum(multiplicity for (selected, hits), multiplicity in ways.items()
                    if selected == draws and hits >= 5)
    expectation = sum(weight * population for weight, population in buckets.items()) * draws / (83 ** 2)
    return numerator / denominator, expectation


def verify(source: Path):
    plan_raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(plan_raw).hexdigest() == saved["plan_sha256"]
    assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"]).decode().strip() == plan["source_revision"]
    rel = "analysis/evidence/boundary_numeric_evidence.json"
    raw = subprocess.check_output(["git", "-C", str(source), "show", f"{plan['source_revision']}:{rel}"])
    assert hashlib.sha256(raw).hexdigest() == saved["source_input_sha256"]
    data = json.loads(raw)
    contexts = [2, 4, 17, 44, 47, 18, 26, 43]
    assert data["contexts"] == saved["numeric_contexts"] == contexts
    product = math.prod(len(data["immediate_post_exception_state_pairs"][str(context)]) for context in contexts)
    assert product == saved["assignment_count"] == 34020
    no_holdout = product // len(data["immediate_post_exception_state_pairs"]["18"])
    assert no_holdout == saved["exact_c18_null"]["training_assignments"] == 3780
    p_value, mean = independent_tail(saved["exact_c18_null"]["multiplicity_histogram"], 9)
    assert math.isclose(p_value, saved["exact_c18_null"]["exact_p_hits_ge_observed"], rel_tol=0, abs_tol=1e-15)
    assert math.isclose(mean, saved["exact_c18_null"]["expected_hits"], rel_tol=0, abs_tol=1e-14)
    assert saved["fit_counts"] == {"4,4":0,"4,5":0,"5,4":0,"5,5":0,"5,6":0,"6,5":0,"6,6":5}
    assert saved["planted_controls"] == {"exact_low_complexity_laws_recovered":2,
                                          "mutated_exact_laws_recovered":0}
    print("PASS: source numeric menus, 34,020 assignments and independently computed exact c18 null tail")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    verify(args.source.resolve())
