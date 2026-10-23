"""Independent manuscript statistics and source-rule audit for Stage U."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FAMILIES = ("English runes", "English prime values", "English Latin A-Z", "decimal digits", "hex digits", "letters A-Z")
VARIANTS = ("I", "T")
STATISTICS = ("pooled", "per-section")
SECTIONS = (7, 8, 9, 11, 12, 13, 14, 15)
ALPHA = 0.0001


def manuscript() -> tuple[float, float]:
    alphabet = {entry["rune"]: entry["index"] for entry in json.loads(
        (ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    assert sorted(alphabet.values()) == list(range(29))
    segments: dict[int, list[int]] = defaultdict(list)
    segment = 7
    for page in range(56):
        raw = json.loads((ROOT / f"data/pages/lp2-{page:02d}.json").read_text(encoding="utf-8"))["raw"]
        for glyph in raw:
            if glyph in alphabet:
                segments[segment].append(alphabet[glyph])
            elif glyph == "$":
                segment += 1
    assert segment == 16
    assert [len(segments[i]) for i in range(7, 16)] == [729, 1145, 1729, 9, 1894, 1021, 1524, 1589, 3316]
    joined = [r for section in range(7, 16) for r in segments[section]]
    assert len(joined) == 12956

    def chi2(runes: list[int]) -> float:
        n = len(runes)
        counts = Counter(runes)
        mean = n / 29
        return sum((counts.get(i, 0) - mean) ** 2 / mean for i in range(29))

    assert chi2(list(range(29)) * 10) == 0
    assert chi2([0] * 29) == 812
    return chi2(joined), sum(chi2(segments[i]) for i in SECTIONS)


def verify() -> dict:
    with (HERE / "source-stage_u_results.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 80
    by = {(r["kind"], r["family"], r["variant"], r["statistic"]): r for r in rows}
    assert len(by) == len(rows)
    for family in FAMILIES:
        gate = by[("gate_G1", family, "I", "pooled")]
        observed = float(gate["value"])
        predicted, verdict = gate["detail"].split()
        assert verdict == "ok" and abs(observed / float(predicted) - 1) <= 0.03 + 0.0002
    factors = {}
    for stat in STATISTICS:
        factors[stat] = float(by[("factor", "flat key", "-", stat)]["value"])
        assert 0 < factors[stat] < 2

    excluded = untestable = not_excluded = 0
    for family in FAMILIES:
        for variant in VARIANTS:
            for stat in STATISTICS:
                power = by[("gate_G2", family, variant, stat)]
                false = by[("gate_G3", family, variant, stat)]
                numerator, denominator = map(int, power["value"].split("/"))
                assert denominator == 20 and 0 <= numerator <= 20
                assert power["detail"] == ("testable" if numerator >= 18 else "untestable")
                assert false["value"] == "0/20" and false["detail"] == "ok"
                lp2 = by[("lp2", family, variant, stat)]
                raw, corrected = (float(v) for v in lp2["value"].split(" / "))
                verdict = lp2["detail"].split(";", 1)[0]
                expected = ("untestable" if numerator < 18 else
                            "EXCLUDED" if raw <= ALPHA and corrected <= ALPHA else "not excluded")
                assert verdict == expected, (family, variant, stat, verdict, expected)
                excluded += verdict == "EXCLUDED"
                untestable += verdict == "untestable"
                not_excluded += verdict == "not excluded"
    pooled, sectioned = manuscript()
    assert abs(pooled - 26.36) < 0.005
    assert abs(sectioned - 194.14) < 0.005
    assert excluded + untestable + not_excluded == 24
    return {"source_rows": len(rows), "families": 6, "settings": 24, "gate_G1_passed": 6,
            "gate_G3_false_exclusions": 0, "excluded": excluded, "untestable": untestable,
            "not_excluded": not_excluded, "pooled_chi2": round(pooled, 2),
            "sectioned_chi2": round(sectioned, 2), "source_factors": factors}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
