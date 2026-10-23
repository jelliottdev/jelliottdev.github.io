"""Run the pinned L2 driver while memoizing its identical seeded null samples.

Only execution is optimized. The source's plant, decoder, p calculation, gates,
and 34-cell traversal remain unchanged. A completed checkpoint can be supplied
to resume an interrupted run after its cells are checked against pinned output.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from check import verify

LANE = Path("analysis/round21/L2-nskips-crossover-length")


def cell_key(row: dict) -> tuple[int, str, str, str]:
    return row["L"], row["mode"], row["mech"], row["register"]


def run(lp: Path, checkpoint: Path | None = None, procs: int = 6) -> dict:
    lp = lp.resolve()
    lane = lp / LANE
    sys.path.insert(0, str(lane))
    c = importlib.import_module("crossover")

    archived = json.loads((lane / "original_nskips_crossover.json").read_text(encoding="utf-8"))
    pinned_rows = {cell_key(row): row for row in archived["points"]}
    complete: dict[tuple[int, str, str, str], dict] = {}
    samples: dict[tuple[int, str, int], list[int]] = {}
    if checkpoint is not None:
        previous = json.loads(checkpoint.read_text(encoding="utf-8"))
        assert previous["v"] == archived["v"] and previous["seed"] == 3301
        for row in previous["points"]:
            key = cell_key(row)
            assert key in pinned_rows and row == pinned_rows[key], f"Unverified checkpoint cell {key}"
            complete[key] = row
            sample_key = row["L"], row["mode"], row["null_M"]
            sample = [int(value) for value, count in row["null_hist"].items()
                      for _ in range(int(count))]
            assert len(sample) == 300
            if sample_key in samples:
                assert sorted(sample) == sorted(samples[sample_key])
            else:
                samples[sample_key] = sample

    source_null = c.wrongkey_null
    source_measure = c.measure_L
    counts = {"checkpoint_cells": len(complete), "new_null_groups": 0,
              "reused_null_groups": 0, "new_cells": 0}

    def memoized_null(L: int, mode: str, M: int, workers: int, chunk: int = 25) -> list[int]:
        key = L, mode, M
        if key in samples:
            counts["reused_null_groups"] += 1
            return samples[key]
        values = source_null(L, mode, M, workers, chunk)
        samples[key] = values
        counts["new_null_groups"] += 1
        return values

    def checked_measure(L: int, mode: str, mech: str, reg: str, workers: int,
                        M: int = c.M_NULL, supp: float = .83) -> dict:
        key = L, mode, mech, reg
        if key in complete:
            return complete[key]
        # Source histograms have integer keys in memory; JSON serializes them
        # as strings. Compare the persisted representation, not Python key types.
        row = json.loads(json.dumps(source_measure(L, mode, mech, reg, workers, M, supp)))
        if row != pinned_rows[key]:
            different = {name: (row.get(name), pinned_rows[key].get(name))
                         for name in row if row.get(name) != pinned_rows[key].get(name)}
            raise AssertionError(f"New source cell differs from pinned result: {key}: {different}")
        counts["new_cells"] += 1
        return row

    c.wrongkey_null = memoized_null
    c.measure_L = checked_measure
    result = c.main(procs=procs)
    assert result["done"] and len(result["points"]) == 34
    report = verify(lp)
    return {**counts, **report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="isolated liber-primus source directory")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--procs", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(run(args.source_root, args.checkpoint, args.procs), indent=2))
