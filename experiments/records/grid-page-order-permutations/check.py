"""Independent necessary-condition check: a page permutation needs 56/57 low bytes in a row."""
import csv
from itertools import groupby
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def max_low_run(data, upper_bound):
    return max((sum(1 for _ in group) for is_low, group in groupby(data, key=lambda x: x < upper_bound) if is_low), default=0)


def main():
    plan = json.loads((ROOT / "experiments/records/grid-direct-bytes/plan.json").read_text(encoding="utf-8"))
    stems = json.loads((ROOT / "experiments/records/grid-stem-uncertainty/results.json").read_text(encoding="utf-8"))["stem_cells"]
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as handle:
        cells = list(csv.DictReader(handle))
    alphabet = plan["digit_alphabet"]
    baseline = [60 * alphabet.index(cell["token"][0]) + alphabet.index(cell["token"][1]) for cell in cells]
    limits = {56: 0, 57: 0}
    count = 0
    for rows_first in (True, False):
        for flip_major in (False, True):
            for flip_minor in (False, True):
                for serpent in (False, True):
                    major_size = 32 if rows_first else 8
                    minor_size = 8 if rows_first else 32
                    order = []
                    for step in range(major_size):
                        major = major_size - 1 - step if flip_major else step
                        for place in range(minor_size):
                            minor = minor_size - 1 - place if flip_minor ^ (serpent and step % 2 == 1) else place
                            order.append(major * 8 + minor if rows_first else minor * 8 + major)
                    for variant in range(1024):
                        values = baseline[:]
                        for bit, stem in enumerate(stems):
                            values[stem["sequence"] - 1] = stem["base60_bytes"][(variant >> bit) & 1]
                        sequence = [values[index] for index in order]
                        count += 1
                        for size in (56, 57):
                            limits[size] = max(limits[size], max_low_run(sequence, size))
    source = (ROOT / "experiments/records/grid-page-order-permutations/source/canon_256.bin").read_bytes()
    assert count == 16384
    assert limits == {56: 3, 57: 5}
    assert max_low_run(source, 56) == 3 and max_low_run(source, 57) == 3
    assert all(limits[n] < n for n in (56, 57))
    print("PASS: independent run-length condition excludes 56/57-page permutations in 16,384 readings; longest runs are 3 and 5")


if __name__ == "__main__":
    main()
