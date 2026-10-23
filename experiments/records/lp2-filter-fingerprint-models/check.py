"""Cross-check the source's model ladder against an independent input analysis."""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def close(a: float, b: float, label: str) -> None:
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10), (label, a, b)


def compare_receipt(a: object, b: object, label: str = '') -> None:
    """Compare all archived fields except tie-sensitive auxiliary AUCs."""
    if isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), label
        for key in a:
            if key != 'auc':
                compare_receipt(a[key], b[key], f'{label}/{key}')
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), label
        for i, (left, right) in enumerate(zip(a, b)):
            compare_receipt(left, right, f'{label}/{i}')
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        close(a, b, label)
    else:
        assert a == b, (label, a, b)


def main() -> None:
    independent = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    archived = json.loads((HERE / "source" / "original_results.json").read_text(encoding="utf-8"))
    fresh = json.loads((HERE / "replay-source.json").read_text(encoding="utf-8"))
    real = fresh["real"]
    compare_receipt(fresh, archived)

    assert independent["pages"] == 55
    assert independent["runes"] == fresh["n"] == 12956
    assert independent["nonempty_physical_lines"] == 594
    assert independent["source_occupied_line_ordinals"] == 648
    assert independent["doublets"] == real["n_doublets"] == 86
    assert independent["doublets_across_lines"] == 4
    assert independent["doublets_across_pages"] == 0
    close(independent["lag_rates"]["lag1"], real["lag1_rate"], "lag1")
    close(independent["lag2_to_8_rate"], real["bleed28_rate"], "lag2-8")
    close(independent["lag2_to_8_z"], real["bleed28_z"], "lag2-8 z")
    close(independent["gap_cv"], real["gap_cv"], "same-rune gap CV")
    close(independent["page_doublet_dispersion"], real["page_rate_dispersion"], "page dispersion")
    close(independent["doublets_across_lines"] / 86,
          real["dbl_line_cross_rate"], "line-cross fraction")
    for width in (29, 58, 116, 290):
        close(independent["window_chi2_over_df"][str(width)],
              real[f"chi2W{width}_mean"], f"window {width}")

    # Check the source replay against its pinned receipt. Named model results
    # carry simulation uncertainty; the exact code, seed and sample count
    # should reproduce them to floating-point tolerance in this environment.
    assert fresh["reps"] == archived["reps"] == 200
    for key in ("lag1_rate", "bleed28_rate", "gap_cv", "chi2W58_mean",
                "page_rate_dispersion", "n_doublets", "dbl_line_cross_rate"):
        close(fresh["real"][key], archived["real"][key], f"archived real {key}")
    assert fresh["gates"]["PASS"] and fresh["gates"]["uniform_vs_machine"]["lag1_z"]["power"] >= .99
    assert fresh["scope_test"]["combined"]["power"] >= .8
    assert fresh["adjudication"]["hand_bleed_none"]["verdict"] == "UNDERPOWERED-TO-SEPARATE"
    assert fresh["adjudication"]["hand_bleed_none"]["combined"]["power"] < .8
    for rung in ("hand_bleed_tiny", "hand_bleed_small", "hand_bleed_mid",
                 "hand_bleed_strong", "hand_rebalance_only"):
        assert fresh["adjudication"][rung]["verdict"] == archived["adjudication"][rung]["verdict"]
        assert fresh["adjudication"][rung]["combined"]["power"] >= .8
    assert fresh["scope_test"]["dbl_line_cross_z"]["power_flat_vs_linescoped"] >= .8
    assert fresh["scope_test"]["dbl_line_cross_z"]["inside_flat_95"]
    assert not fresh["scope_test"]["dbl_line_cross_z"]["inside_linescoped_95"]
    assert fresh["bleed_bound"]["max_lag2to8_suppression_at_95pct"] < .03
    print("PASS: independent runes/window/gap/line checks and source control gates")


if __name__ == "__main__":
    main()
