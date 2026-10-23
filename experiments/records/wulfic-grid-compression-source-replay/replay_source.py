"""Rerun only pinned Wulfic Stage X4 and compare the committed X4 rows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
HEADER = ("part", "test", "reading", "value", "reference", "detail", "verdict")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tsv(rows: list[tuple[str, ...]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clone", type=Path)
    args = parser.parse_args()
    clone = args.clone.resolve()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    rev = subprocess.check_output(["git", "-C", str(clone), "rev-parse", "HEAD"], text=True).strip()
    assert rev == plan["source"]["commit"]
    for file, field in (("tools/run_stage_x.py", "stage_x_sha256"),
                        ("tools/run_stage_n.py", "stage_n_sha256")):
        assert sha((clone / file).read_bytes()) == plan["source"][field], file
    original = subprocess.check_output(["git", "-C", str(clone), "show",
                                        "HEAD:reference/findings/stage_x_other.tsv"])
    assert sha(original) == plan["source"]["published_full_other_sha256"]
    source_rows = list(csv.reader(io.StringIO(original.decode("utf-8")), delimiter="\t"))
    assert tuple(source_rows[0]) == HEADER
    expected = [tuple(row) for row in source_rows[1:] if row[0] == "X4"]
    assert len(expected) == 24
    sys.path.insert(0, str(clone))
    from tools.lpcore import keys
    from tools.lpcore.corpus import load_corpus
    from tools import run_stage_x as x
    grid = np.array(keys.grid_bytes(load_corpus()), dtype=np.uint8)
    assert grid.shape == (256,)
    rows = [tuple(map(str, row)) for row in x.x4_rows(grid, 100_000)]
    if rows != expected:
        for position, (actual, source) in enumerate(zip(rows, expected)):
            if actual != source:
                raise ValueError(f"Stage X4 row {position} differs: {actual!r} vs {source!r}")
        raise ValueError(f"Stage X4 row count differs: {len(rows)} vs {len(expected)}")
    content = tsv(rows)
    (HERE / "source-stage_x4_rows.tsv").write_bytes(content)
    print(f"Stage X4 exact component: {len(rows)} rows byte-identical; sha256 {sha(content)}")


if __name__ == "__main__":
    main()
