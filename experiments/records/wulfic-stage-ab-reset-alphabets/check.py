"""Independent manuscript reconstruction and Stage AB statistic check."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KINDS = ("segment", "paragraph", "clause", "line", "page")


def manuscript() -> tuple[list[int], dict[str, list[int]]]:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {entry["rune"]: entry["index"] for entry in index["alphabet"]}
    names = {kind: 0 for kind in KINDS}
    runes: list[int] = []
    unit_ids: dict[str, list[int]] = {kind: [] for kind in KINDS}
    for page in range(56):
        names["page"] = page
        document = json.loads((ROOT / f"data/pages/lp2-{page:02}.json").read_text(encoding="utf-8"))
        for ch in document["raw"]:
            if ch in alphabet:
                runes.append(alphabet[ch])
                for kind in KINDS:
                    unit_ids[kind].append(names[kind])
            elif ch == ".":
                names["clause"] += 1
            elif ch == "&":
                names["clause"] += 1
                names["paragraph"] += 1
            elif ch == "$":
                names["clause"] += 1
                names["segment"] += 1
            elif ch == "/":
                names["line"] += 1
        # The source parser treats every page edge as a line boundary even
        # when a word continues across that edge.
        names["line"] += 1
    return runes, unit_ids


def summarize(ids: list[int]) -> tuple[list[int], list[int]]:
    lengths: list[int] = []
    positions: list[int] = []
    prior = None
    for identity in ids:
        if identity != prior:
            lengths.append(0)
            prior = identity
        positions.append(lengths[-1])
        lengths[-1] += 1
    return lengths, positions


def pairs_by_group_and_symbol(runes: list[int], positions: list[int]) -> int:
    bucket: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, (rune, pos) in enumerate(zip(runes, positions, strict=True)):
        bucket[pos, rune].append(index)
    return sum(len(indices) * (len(indices) - 1) // 2 for indices in bucket.values())


def main() -> None:
    source_runes, unit_ids = manuscript()
    saved = json.loads((HERE / "layout.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert source_runes == saved["runes"] and len(source_runes) == 12956
    assert set(saved["unit_lengths"]) == set(KINDS)
    assert [row["unit"] for row in result["rows"]] == list(KINDS)
    with (HERE / "source-stage_ab_results.tsv").open(encoding="utf-8", newline="") as f:
        source_rows = list(csv.DictReader(f, delimiter="\t"))
    with (HERE / "source-stage_ab_controls.tsv").open(encoding="utf-8", newline="") as f:
        controls = list(csv.DictReader(f, delimiter="\t"))
    assert len(source_rows) == 5 and len(controls) == 10
    for row, upstream in zip(result["rows"], source_rows, strict=True):
        kind = row["unit"]
        lengths, positions = summarize(unit_ids[kind])
        assert lengths == saved["unit_lengths"][kind]
        observed = pairs_by_group_and_symbol(source_runes, positions)
        assert observed == row["observed_pairs"] == int(upstream["K_LP2"])
        # Independent analytic null: for each position, choose pairs among
        # units reaching it; each pair agrees with probability 1/29.
        expected = sum(sum(a > t for a in lengths) * (sum(a > t for a in lengths) - 1) / 58
                       for t in range(max(lengths)))
        assert abs(expected - row["analytic_flat_mean"]) < 0.000001
        assert abs(expected - float(upstream["analytic_mean"])) < 0.001
        assert observed < min(float(upstream["E_lower"]), float(upstream["L_lower"]))
        assert float(upstream["null_mean"]) < min(float(upstream["E_lower"]), float(upstream["L_lower"]))
        assert upstream["verdict"] == "EXCLUDED"
        planted = [float(c["min"]) for c in controls if c["unit"] == kind]
        assert len(planted) == 2 and min(planted) > int(upstream["null_max"])
    # Positive control of the invariant itself: one fixed permutation at
    # every in-unit position preserves equal plaintext at that position.
    plain = [1, 2, 1, 3, 1, 2, 1, 4]
    positions = [0, 1, 2, 3, 0, 1, 2, 3]
    encrypted = [(p + 7 * pos + 3) % 29 for p, pos in zip(plain, positions)]
    assert pairs_by_group_and_symbol(plain, positions) == 3
    assert pairs_by_group_and_symbol(encrypted, positions) == 3
    print("Independent page, boundary, K and planted invariant checks: OK")


if __name__ == "__main__":
    main()
