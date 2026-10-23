"""Summarize exact Stage AA/Z repeat-preservation source tables."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def build() -> dict:
    aa_counts = table("source-stage_aa_results.tsv")
    aa_widths = table("source-stage_aa_verdicts.tsv")
    aa_controls = table("source-stage_aa_controls.tsv")
    z_counts = table("source-stage_z_results.tsv")
    z_controls = table("source-stage_z_controls.tsv")
    assert len(aa_counts) == 10 and len(aa_widths) == 26 and len(aa_controls) == 260
    assert len(z_counts) == 72 and len(z_controls) == 144
    assert {row["verdict"] for row in aa_counts} <= {"NO PASS", "PASS", "VOID"}
    assert {row["verdict"] for row in aa_widths} <= {"EXCLUDED", "INCONCLUSIVE", "UNTESTABLE", "VOID"}
    assert {row["verdict"] for row in z_counts} <= {"EXCLUDED", "INCONCLUSIVE", "UNTESTABLE", "PASS", "VOID"}
    assert {int(row["draws"]) for row in aa_controls + z_controls} == {200}
    for row in aa_counts + z_counts:
        assert int(row["K_LP2"]) >= 0
    return {
        "schema": "liberpedia-wulfic-local-codebook-results-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "source_commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
        "source_tables": {name: sha(HERE / name) for name in (
            "source-stage_aa_results.tsv", "source-stage_aa_verdicts.tsv",
            "source-stage_aa_controls.tsv", "source-stage_z_results.tsv", "source-stage_z_controls.tsv")},
        "aa": {
            "statistic_cells": len(aa_counts),
            "statistic_verdicts": dict(sorted(Counter(row["verdict"] for row in aa_counts).items())),
            "width_cells": len(aa_widths),
            "width_verdicts": dict(sorted(Counter(row["verdict"] for row in aa_widths).items())),
            "width_rows": [{key: row[key] for key in ("mode", "w", "verdict", "excluded_by_n")}
                           for row in aa_widths],
            "control_rows": len(aa_controls),
        },
        "z": {
            "cells": len(z_counts),
            "verdicts": dict(sorted(Counter(row["verdict"] for row in z_counts).items())),
            "word_cells": [{key: row[key] for key in ("cell", "K_LP2", "null_max", "E_lower", "L_lower", "verdict")}
                           for row in z_counts if row["cell"].startswith("Zw-")],
            "block_by_length": [
                {"n": n, "total": sum(r["cell"].startswith(f"Zb-{n}-") for r in z_counts),
                 "verdicts": dict(sorted(Counter(r["verdict"] for r in z_counts
                                                 if r["cell"].startswith(f"Zb-{n}-")).items()))}
                for n in range(2, 9)],
            "control_rows": len(z_controls),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    path = HERE / "results.json"
    if args.check:
        assert path.read_text(encoding="utf-8") == rendered
        print("Wulfic AA/Z source tables: OK")
    else:
        path.write_text(rendered, encoding="utf-8", newline="\n")
