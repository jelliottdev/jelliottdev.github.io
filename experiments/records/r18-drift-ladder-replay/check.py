"""Independent page mapping, bound arithmetic, and source-replay receipt checks."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def numeric_equal(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(numeric_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(numeric_equal(x, y) for x, y in zip(a, b))
    return a == b


def candidate_key(row):
    return json.dumps(row["cand"], sort_keys=True, separators=(",", ":"))


def main():
    source_gate = read("source-gate_F0.json")
    replay_gate = read("replayed-gate_F0.json")
    assert source_gate["pass"] and source_gate["cases"] == 24
    assert source_gate["path_mismatches"] == 0
    assert numeric_equal({k: v for k, v in source_gate.items() if k != "elapsed_s"},
                         {k: v for k, v in replay_gate.items() if k != "elapsed_s"})

    control = read("source-b4_control.json")
    control_replay = read("replayed-b4_control.json")
    assert numeric_equal(control, control_replay)
    assert control["pass"] and [r["rank_of_true_offset"] for r in control["results"]] == [1] * 3

    # The source labels its 55 nonempty segments 0..54. The archival page LP2-50
    # is image-only; all later source ordinals map to the next manuscript page ID.
    pages = []
    for i in range(56):
        page = json.loads((ROOT / "data/pages" / f"lp2-{i:02}.json").read_text(encoding="utf-8"))
        if page["rune_count"]:
            pages.append((page["id"], page["rune_count"]))
    assert len(pages) == 55 and sum(n for _, n in pages) == 12956
    assert pages[52][0] == "lp2-53"
    starts = []
    total = 0
    for _, n in pages:
        starts.append(total)
        total += n
    assert [starts[i] for i in (10, 30, 52)] == [2397, 7307, 12469]
    for row in control["results"]:
        assert row["start"] == starts[row["page"]]
        assert row["true_offset_inside_ladder"]
        assert row["score_at_true_offset"] > row["best_decoy_score"]
        assert row["score_at_true_offset"] > row["score_at_uncorrected_start"]

    source = read("source-b4_ladder.json")
    replay = read("replayed-b4_ladder.json")
    q, suppression = 1 / 29, 0.8129
    rho = q * suppression / (1 - q * suppression)
    variance = q * suppression / (1 - q * suppression) ** 2
    assert math.isclose(source["rho"], rho, rel_tol=1e-14)
    assert source["seg_len"] == replay["seg_len"] == 100
    assert source["n_candidates"] == replay["n_candidates"] == 230
    assert source["ladder_points_per_candidate"] == replay["ladder_points_per_candidate"] == 5961
    assert source["n_decodes"] == replay["n_decodes"] == 1371030
    # Independently derive the number of tested offsets from canonical page lengths.
    points = 0
    for st in starts:
        radius = max(4, math.ceil(4 * math.sqrt(st * variance)))
        center = round(st + rho * st)
        offsets = set(range(max(0, center - radius), center + radius + 1)) | {st, 0}
        points += len(offsets)
    assert points == 5961

    sr = {candidate_key(r): r for r in source["rows"]}
    rr = {candidate_key(r): r for r in replay["rows"]}
    assert len(sr) == len(rr) == 230 and sr.keys() == rr.keys()
    for key in sr:
        assert numeric_equal(sr[key], rr[key]), key
        assert rr[key]["n_decodes"] == 5961
    all_best = max((r["best"][0], r["best"][1], r["best"][4]) for r in rr.values())
    assert all_best[0] < -5.5
    # Some candidates' best is a control; their top-eight retains corrected rows.
    corrected = max(x[0] for r in rr.values() for x in r["top8"] if x[4] == "corrected")
    assert corrected < -5.5

    print("PASS: F0, planted controls, canonical page mapping, and 1,371,030 source decodes")


if __name__ == "__main__":
    main()
