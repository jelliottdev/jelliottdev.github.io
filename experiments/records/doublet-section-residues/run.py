"""Recount doublet positions modulo 2–8 with section-conditioned placement controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SECTIONS = [(0, 2), (3, 7), (8, 14), (15, 22), (23, 26), (27, 32), (33, 39), (40, 53), (54, 55)]
MODULI = tuple(range(2, 9))
TRIALS = 5000
SEED = 3301


def count_mod(events: list[list[int]], modulus: int) -> list[int]:
    counts = [0] * modulus
    for section in events:
        for position in section:
            counts[position % modulus] += 1
    return counts


def chi_over_df(counts: list[int], expected: list[float]) -> float:
    chi = sum((actual - mean) ** 2 / mean for actual, mean in zip(counts, expected))
    return chi / (len(counts) - 1)


def calculate() -> dict:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
    streams = [[alphabet[rune] for page in range(lo, hi + 1)
                for rune in (ROOT / f"text/lp2-{page:02}.txt").read_text(encoding="utf-8") if rune in alphabet]
               for lo, hi in SECTIONS]
    events = [[position for position in range(1, len(stream)) if stream[position] == stream[position - 1]]
              for stream in streams]
    assert [len(stream) for stream in streams] == [729, 1145, 1729, 1903, 1021, 1433, 1680, 3008, 308]
    assert sum(map(len, events)) == 86
    expected = {}
    observed = {}
    for modulus in MODULI:
        means = [sum(len(ev) * sum(i % modulus == remainder for i in range(1, len(stream))) / (len(stream) - 1)
                     for stream, ev in zip(streams, events)) for remainder in range(modulus)]
        expected[str(modulus)] = means
        counts = count_mod(events, modulus)
        observed[str(modulus)] = {"counts": counts, "chi_over_df": round(chi_over_df(counts, means), 8)}
    best_observed = max(row["chi_over_df"] for row in observed.values())
    rng = random.Random(SEED)
    control_maxima = []
    control_scores = {str(m): [] for m in MODULI}
    for _ in range(TRIALS):
        sample = [rng.sample(range(1, len(stream)), len(ev)) for stream, ev in zip(streams, events)]
        scores = {str(m): chi_over_df(count_mod(sample, m), expected[str(m)]) for m in MODULI}
        for key, value in scores.items():
            control_scores[key].append(round(value, 8))
        control_maxima.append(round(max(scores.values()), 8))
    planted = [list(ev) for ev in events]
    # Keep each section's event count but force all positions onto the seven-step grid.
    planted = [[i for i in range(1, len(stream)) if i % 7 == 0][:len(ev)] for stream, ev in zip(streams, events)]
    assert all(len(a) == len(b) for a, b in zip(planted, events))
    planted7 = chi_over_df(count_mod(planted, 7), expected["7"])
    paths = ["data/index.json"] + [f"text/lp2-{i:02}.txt" for i in range(56)]
    return {
        "schema": "liberpedia-doublet-section-residues-v1",
        "inputs_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "section_lengths": [len(stream) for stream in streams],
        "events_per_section": [len(ev) for ev in events], "total_doublets": sum(map(len, events)),
        "event_positions": events, "opportunity_counts": [len(stream) - 1 for stream in streams],
        "expected_counts": {key: [round(value, 6) for value in values] for key, values in expected.items()},
        "observed": observed, "best_observed_chi_over_df": best_observed,
        "null": "Within each section, sample the same number of doublet-second-rune positions uniformly without replacement from eligible positions 1..n-1; repeat the seven-modulus scan.",
        "seed": SEED, "trials": TRIALS,
        "control_max_chi_over_df": control_maxima,
        "control_by_modulus": control_scores,
        "max_controls_at_least_observed": sum(value >= best_observed for value in control_maxima),
        "planted_mod7_chi_over_df": round(planted7, 8),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    target = HERE / "results.json"
    if args.check:
        assert result == json.loads(target.read_text(encoding="utf-8"))
        print("doublet-section-residues: checked")
    else:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print({"observed": result["observed"], "max_controls_at_least_observed": result["max_controls_at_least_observed"], "planted_mod7": result["planted_mod7_chi_over_df"]})


if __name__ == "__main__":
    main()
