"""Check the T1 batch receipt's files, source parity, and reported counts."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path


REV = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
PREFIX = "liber-primus/analysis/round19/T1/"


def source_json(source_repo: Path, name: str) -> dict:
    raw = subprocess.check_output(
        ["git", "show", f"{REV}:{PREFIX}{name}"], cwd=source_repo
    )
    return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[4]
    receipt = json.loads((Path(__file__).parent / "receipt.json").read_text())
    assert receipt["source_revision"] == REV
    files = {}
    for entry in receipt["entries"]:
        for item in entry["evidence"]:
            path = repo / item["path"]
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item["sha256"], path
            files[path.name] = path

    for name in ("out_gread_lp2.json", "out_gread_lp1.json", "out_loo.json", "out_segcheck.json", "out_corpus_lp2.json", "adjudication.json", "out_density.json", "out_summary.json"):
        if name in files:
            assert json.loads(files[name].read_text()) == source_json(args.source_repo, name), name

    g = json.loads(files["out_gread_lp2.json"].read_text())["lp2"]
    assert [(r["correct"], r["canon"]) for r in g["rows"]] == [(85, 85), (95, 95)]
    assert (g["n_correct"], g["n_canon"]) == (180, 180)
    loo = json.loads(files["out_loo.json"].read_text())
    triple = ("O", "A", "AE")
    assert sum(loo["oae"]["recall_" + r]["of"] for r in triple) == 1404
    assert all(loo["oae"][f"{a}->{b}"]["n"] == 0 for a in triple for b in triple if a != b)
    seg = json.loads(files["out_segcheck.json"].read_text())["summary"]
    assert (seg["lp2_segmented"], seg["lp2_canon"]) == (12946, 13041)
    y_rows = re.findall(
        r"^([A-Z]+)\s+n=\s*(\d+)\s+->\s+(\{[^}]+\})",
        files["ycomp.log"].read_text(),
        re.MULTILINE,
    )
    assert len(y_rows) == 29
    assert next((int(n), counts) for label, n, counts in y_rows if label == "Y") == (55, "{1: 55}")
    assert sum(int(n) for label, n, _ in y_rows if label != "Y") == 1398
    assert all(counts == "{0: %d}" % int(n) for label, n, counts in y_rows if label != "Y")

    if "out_corpus_lp2.json" in files:
        corpus = json.loads(files["out_corpus_lp2.json"].read_text())
        assert corpus["n_canon"] == sum(row["canon"] for row in corpus["pages"])
        assert corpus["n_equal"] == sum(row["correct"] for row in corpus["pages"])
        assert abs(corpus["agreement"] - 100 * corpus["n_equal"] / corpus["n_canon"]) < 1e-9
    if "adjudication.json" in files:
        adjudication = json.loads(files["adjudication.json"].read_text())
        assert adjudication["n_records"] == len(adjudication["rows"]) == 450
        assert adjudication["tally"] == dict(collections.Counter(row["verdict"] for row in adjudication["rows"]))
        for row in adjudication["rows"]:
            assert row["verdict"] == "AGREE"
            assert row["t1_call"] == row["canon_call"]
            assert row["margin"] is None or row["margin"] >= adjudication["cut"]
    print("PASS: T1 evidence hashes, pinned source JSON and independent count checks")


if __name__ == "__main__":
    main()
