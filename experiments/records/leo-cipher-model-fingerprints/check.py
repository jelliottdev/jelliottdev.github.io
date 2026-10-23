"""Check preserved model rows against a fresh upstream run and verify the chain identity."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SOURCE_ROW = re.compile(r"^(.+?)\s+(0\.\d{4})\s+(\d\.\d{3})\s+(\d+\.\d)\s+(0\.\d{4})(?:\s+<== TARGET.*)?$")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_rows(text):
    result = {}
    for line in text.splitlines():
        match = SOURCE_ROW.match(line)
        if match:
            result[match.group(1).strip()] = tuple(match.groups()[1:])
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, required=True)
    args = p.parse_args()
    root = args.source_root.resolve()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    for name, key in (
        ("fingerprint.py", "source_script_sha256"),
        ("lp.py", "source_lp_sha256"),
        ("dataset.json", "source_dataset_sha256"),
        ("results/fingerprint.txt", "source_receipt_sha256"),
        ("sources/relikd_LiberPrayground/data/baseline-rune-stream.txt", "baseline_rune_stream_sha256"),
        ("sources/relikd_LiberPrayground/data/baseline-rune-words.txt", "baseline_rune_words_sha256"),
    ):
        assert digest(root / name) == plan[key], name
    assert saved["plan_sha256"] == digest(HERE / "plan.json")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    fresh = subprocess.run([sys.executable, "fingerprint.py"], cwd=root, env=env, capture_output=True, text=True, check=True)
    fresh_rows = parse_rows(fresh.stdout)
    archived_rows = parse_rows((root / "results/fingerprint.txt").read_text(encoding="utf-8"))
    assert fresh_rows == archived_rows and len(fresh_rows) == 24
    assert len(saved["models"]) == 23
    for model in saved["models"]:
        assert tuple(model["archived_display"]) == fresh_rows[model["name"]]
        assert model["equal1"] >= 0 and model["runes"] == 2979

    dataset = json.loads((root / "dataset.json").read_text(encoding="utf-8"))
    plain = [symbol for sec in dataset["sections"] if sec["solved"] for symbol in sec["plain_indices"]]
    cipher = [symbol for sec in dataset["sections"] if not sec["solved"] for symbol in sec["indices"]]
    assert len(plain) == 2979 and len(cipher) == 12956
    observed_equal = sum(cipher[i] == cipher[i - 1] for i in range(1, len(cipher)))
    assert saved["observed"]["equal1"] == observed_equal == 86
    counts = Counter(plain[1:])
    candidates = []
    for b in range(29):
        # Independent recurrence check plus the mathematical count identity.
        previous = 0
        sequence = []
        for symbol in plain:
            previous = (previous + symbol + b) % 29
            sequence.append(previous)
        matches = sum(sequence[i] == sequence[i - 1] for i in range(1, len(sequence)))
        expected = counts[(-b) % 29]
        row = saved["offset_followup"][b]
        assert matches == expected == row["count"]
        assert row["offset"] == b and row["repeat_symbol"] == (-b) % 29
        assert abs(row["rate"] - matches / (len(plain) - 1)) < 1e-15
        candidates.append((abs(matches / (len(plain) - 1) - observed_equal / (len(cipher) - 1)), b))
        if b == 1:
            reconstructed = [(sequence[0] - 1) % 29] + [(sequence[i] - sequence[i - 1] - 1) % 29 for i in range(1, len(sequence))]
            assert reconstructed == plain
    assert sorted(candidates).index(next(row for row in candidates if row[1] == 1)) + 1 == saved["source_offset_rank_by_absolute_rate_distance"] == 1
    chain = next(m for m in saved["models"] if m["name"] == "chain c=c_prev+p+1")
    assert chain["equal1"] == 20
    print("Fresh upstream 23-row receipt, inverse control, and all 29 independent count identities checked.")


if __name__ == "__main__":
    main()
