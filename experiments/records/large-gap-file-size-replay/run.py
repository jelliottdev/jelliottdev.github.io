"""Replay one archived big-gap post's file-size comparison without refitting groups."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    big = plan["reported_big_gap_lp2_pages"]
    regular = plan["reported_regular_gap_comparison_lp2_pages"]
    assert len(big) == 16 and len(regular) == 15 and len(set(big + regular)) == 31
    rows = []
    for i in range(58):
        path = ROOT / "images" / f"lp2-{i:02d}.jpg"
        rows.append({"page": f"lp2-{i:02d}", "bytes": path.stat().st_size, "sha256": sha(path),
                     "reported_class": "big" if i in big else "regular_sample" if i in regular else "unselected"})
    by_page = {i: rows[i]["bytes"] for i in range(58)}
    bsize = [by_page[i] for i in big]
    rsize = [by_page[i] for i in regular]
    printed = plan["reported_size_kb_in_order"]
    reported_mean_b = statistics.mean(printed["big_gap"])
    reported_mean_r = statistics.mean(printed["regular_gap"])
    actual_diff = statistics.mean(bsize) - statistics.mean(rsize)
    pooled = bsize + rsize
    rng = random.Random(plan["random_seed"])
    abs_ge = 0
    one_ge = 0
    diffs = []
    for _ in range(plan["permutation_trials"]):
        chosen = set(rng.sample(range(31), 16))
        trial_b = [v for j, v in enumerate(pooled) if j in chosen]
        trial_r = [v for j, v in enumerate(pooled) if j not in chosen]
        d = statistics.mean(trial_b) - statistics.mean(trial_r)
        diffs.append(d)
        one_ge += d >= actual_diff
        abs_ge += abs(d) >= abs(actual_diff)
    observed = {
        "reported_arithmetic": {"big_mean_kb": reported_mean_b, "regular_mean_kb_corrected": reported_mean_r,
                                "regular_mean_kb_claimed": 508.9375, "difference_kb_corrected": reported_mean_b - reported_mean_r,
                                "difference_kb_claimed_approx": 74},
        "archived_image_bytes": {"big_mean": statistics.mean(bsize), "regular_mean": statistics.mean(rsize),
                                 "mean_difference": actual_diff, "all_58_mean": statistics.mean(r["bytes"] for r in rows),
                                 "big_median": statistics.median(bsize), "regular_median": statistics.median(rsize)},
        "reported_kb_match_with_archived": {"unit": "ceil(bytes / 1024), as apparent from all supplied values",
                                            "big": [math.ceil(v / 1024) == k for v, k in zip(bsize, printed["big_gap"])],
                                            "regular": [math.ceil(v / 1024) == k for v, k in zip(rsize, printed["regular_gap"])]},
        "fixed_label_permutation_reference": {"trials": len(diffs), "seed": plan["random_seed"],
                                              "one_sided_ge": one_ge, "absolute_ge": abs_ge,
                                              "one_sided_fraction": one_ge / len(diffs),
                                              "two_sided_fraction": abs_ge / len(diffs),
                                              "central_95_byte_range": [sorted(diffs)[2500], sorted(diffs)[97500]]},
        "pages": rows,
    }
    target = HERE / "results.json"
    payload = json.dumps(observed, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        assert target.read_text(encoding="utf-8") == payload, "results.json does not match recomputation"
    else:
        target.write_text(payload, encoding="utf-8")
    print(f"source printed means {reported_mean_b:.4f} vs {reported_mean_r:.4f} KB; archived mean difference {actual_diff / 1024:.2f} KiB")
    print(f"fixed-label reference >= observed: {one_ge}/{len(diffs)}")


if __name__ == "__main__":
    main()
