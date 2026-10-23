"""Independent framing audit for the 0xCB starts in LP2 grid byte routes."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main():
    plan = json.loads((ROOT / "experiments/records/grid-direct-bytes/plan.json").read_text(encoding="utf-8"))
    stems = json.loads((ROOT / "experiments/records/grid-stem-uncertainty/results.json").read_text(encoding="utf-8"))["stem_cells"]
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as handle:
        entries = list(csv.DictReader(handle))
    alphabet = plan["digit_alphabet"]
    values0 = [60 * alphabet.index(entry["token"][0]) + alphabet.index(entry["token"][1]) for entry in entries]
    starts, no_start = 0, 0
    ends = set()
    for by_column in (False, True):
        for reverse_outer in (False, True):
            for reverse_inner in (False, True):
                for alternate in (False, True):
                    height, width = (8, 32) if by_column else (32, 8)
                    positions = []
                    for step in range(height):
                        outer = height - 1 - step if reverse_outer else step
                        for position in range(width):
                            inner = width - 1 - position if reverse_inner ^ (alternate and step % 2 == 1) else position
                            positions.append(inner * 8 + outer if by_column else outer * 8 + inner)
                    for mask in range(1 << len(stems)):
                        values = values0.copy()
                        for bit, stem in enumerate(stems):
                            values[stem["sequence"] - 1] = stem["base60_bytes"][(mask >> bit) & 1]
                        stream = bytes(values[i] for i in positions)
                        if stream[0] != 0xCB:
                            no_start += 1
                            continue
                        starts += 1
                        # CB is tag 11. Rows have an E7 128-byte partial
                        # segment; columns have a one-octet definite length.
                        if stream[1] == 0xE7:
                            final_length_octet = stream[130]
                            assert final_length_octet < 192
                            consumed = 131 + final_length_octet
                        else:
                            assert stream[1] < 192
                            consumed = 2 + stream[1]
                        assert consumed < len(stream), "The packet unexpectedly consumes the whole stream"
                        ends.add(consumed)
    assert (starts, no_start) == (4096, 12288)
    print(f"PASS: all {starts} tag-11 starts terminate before byte 256 (end offsets {sorted(ends)})")


if __name__ == "__main__":
    main()
