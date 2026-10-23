"""Conditional rejection-channel law, derived without the unavailable source corpora."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def build():
    plan = json.loads((HERE / "plan.json").read_text())
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    n = 29
    pairs = 12955
    repeats = 86
    length = 12956
    rate = repeats / pairs
    skip_s = (1 - n * rate) / (1 - rate)
    rewrite_s = n * (1 - n * rate) / (n - 1)
    assert 0 <= skip_s <= 1 and 0 <= rewrite_s <= 1
    q = skip_s / n
    repeat_prob = (1 - skip_s) / (n - skip_s)
    other_prob = 1 / (n - skip_s)
    assert math.isclose(repeat_prob, rate, abs_tol=1e-15)
    assert math.isclose(repeat_prob + (n - 1) * other_prob, 1, abs_tol=1e-15)
    assert math.isclose((1 - rewrite_s) / n + rewrite_s / n**2, rate, abs_tol=1e-15)
    expected_extra = pairs * q / (1 - q)
    extra_sd = math.sqrt(pairs * q / (1 - q) ** 2)
    source = json.loads((HERE / "source/c_budget.json").read_text())
    drift = json.loads((HERE / "source/b_drawcount.json").read_text())
    return {
        "schema": "liberpedia-rejection-channel-information-v1",
        "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
        "source_ids": plan["source_ids"],
        "alphabet_size": n, "rune_count": length, "adjacent_pairs": pairs,
        "observed_equal_pairs": repeats, "observed_repeat_rate": rate,
        "skip_s_fitted": skip_s, "rewrite_s_fitted": rewrite_s,
        "skip_rejection_probability_per_draw": q,
        "repeat_probability": repeat_prob,
        "each_other_symbol_probability": other_prob,
        "independent_of_plaintext": True,
        "equivalent_visible_markov_law": True,
        "expected_extra_draws": expected_extra,
        "extra_draws_sd": extra_sd,
        "source_fixed_s": 0.8129,
        "source_fixed_s_expected_extra": pairs * (0.8129 / n) / (1 - 0.8129 / n),
        "matches_source_closed_rate": abs((1 - 0.8129) / (n - 0.8129)
                                          - source["acceptance_channel"]["closed_form_residual_rate"]) < 1e-14,
        "matches_source_drift_mean": abs(pairs * (0.8129 / n) / (1 - 0.8129 / n)
                                         - drift["B1"]["analytic_mean_extra_draws"]) < 1e-10,
        "scope_note": "A conditional theorem for an iid uniform independent key and the specified filters; not a replay of source English-corpus simulations or a claim that LP2 uses either filter."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text())
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("repeat", round(result["repeat_probability"], 8), "extra draws", round(result["expected_extra_draws"], 1))


if __name__ == "__main__":
    main()
