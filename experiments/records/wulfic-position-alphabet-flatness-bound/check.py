"""Independent manuscript counts and decision checks for Wulfic Stage T.

The historical Monte Carlo experiment remains in the pinned upstream program.
This checker uses Liberpedia's page JSON, not the upstream corpus parser.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SECTIONS = (7, 8, 9, 11, 12, 13, 14, 15)
ALPHA = 0.0001


def cdf_even(x: float, df: int = 28) -> float:
    """Lower tail of an even-degree central chi-square, summed stably."""
    assert df > 0 and df % 2 == 0
    if x <= 0:
        return 0.0
    h = x / 2
    j = df // 2
    term = total = 1.0
    while term > total * 1e-17:
        j += 1
        term *= h / j
        total += term
    return min(1.0, math.exp((df // 2) * math.log(h) - h - math.lgamma(df // 2 + 1)) * total)


def chi2(runes: list[int]) -> float:
    n = len(runes)
    assert n > 0
    counts = Counter(runes)
    expected = n / 29
    return sum((counts.get(i, 0) - expected) ** 2 / expected for i in range(29))


def site_sections() -> dict[int, list[int]]:
    alphabet = {entry["rune"]: entry["index"] for entry in json.loads(
        (ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    assert sorted(alphabet.values()) == list(range(29))
    sections: dict[int, list[int]] = defaultdict(list)
    current = 7
    for page in range(56):
        raw = json.loads((ROOT / f"data/pages/lp2-{page:02d}.json").read_text(encoding="utf-8"))["raw"]
        for glyph in raw:
            if glyph in alphabet:
                sections[current].append(alphabet[glyph])
            elif glyph == "$":
                current += 1
    assert current == 16 and not sections[16]  # final delimiter closes section 15
    assert [len(sections[i]) for i in range(7, 16)] == [729, 1145, 1729, 9, 1894, 1021, 1524, 1589, 3316]
    return sections


def records() -> list[dict[str, str]]:
    with (HERE / "source-stage_t_results.tsv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def row(rows: list[dict[str, str]], kind: str, name: str) -> dict[str, str]:
    hits = [item for item in rows if item["kind"] == kind and item["name"] == name]
    assert len(hits) == 1, (kind, name)
    return hits[0]


def close_printed(actual: float, displayed: str, places: int = 2) -> None:
    assert abs(actual - float(displayed)) <= 0.5 * 10 ** -places + 1e-7, (actual, displayed)


def verify() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    rows = records()
    assert len(rows) == 45
    sections = site_sections()
    joined = [r for i in range(7, 16) for r in sections[i]]
    pooled = chi2(joined)
    selected = [chi2(sections[i]) for i in SECTIONS]
    section_sum = sum(selected)
    assert len(joined) == 12956
    assert sum(len(sections[i]) for i in SECTIONS) == 12947
    close_printed(pooled, row(rows, "lp2", "pooled chi2")["statistic"])
    close_printed(section_sum, row(rows, "lp2", "per-section sum chi2")["statistic"])
    for section, statistic in zip(SECTIONS, selected):
        source = row(rows, "lp2_section", str(section))
        assert int(source["V_or_n"]) == len(sections[section])
        close_printed(statistic, source["statistic"])
    assert abs(cdf_even(pooled) - float(row(rows, "lp2", "pooled chi2")["value"])) < 0.0001

    # Source's analytic pooled rule, recalculated independently at the two
    # neighboring integer class counts. The sectioned Monte Carlo bound is
    # checked by the optional exact upstream replay, not rebranded as analytic.
    s = plan["solved_plaintext_coincidence"]
    def pooled_p(v: int) -> float:
        scale = 1 + len(joined) * (29 * s - 1) / (28 * v)
        return cdf_even(pooled / scale)
    assert pooled_p(168) <= ALPHA < pooled_p(169)
    assert int(row(rows, "boundary", "pooled (one tabula)")["V_or_n"]) == 168
    assert int(row(rows, "boundary", "per-section (fresh tabula)")["V_or_n"]) == 174

    # The declared controls must pass before their manuscript conclusions are used.
    for v in (29, 256, 1024):
        gate = row(rows, "gate_A", f"V={v}")
        assert gate["verdict"] == "ok"
        assert abs(float(gate["statistic"]) / float(gate["value"]) - 1) <= 0.15
    gate = row(rows, "gate_B", "V=1024")
    assert gate["verdict"] == "ok" and int(gate["statistic"]) == 0
    assert float(gate["value"]) <= 0.10

    named = [r for r in rows if r["kind"] == "named"]
    assert len(named) == 20
    for item in named:
        p = float(item["value"])
        assert item["verdict"] == ("EXCLUDED" if p <= ALPHA else "not excluded")
    # Two trivial fixtures catch swapped alphabet size/count and sign errors.
    assert chi2(list(range(29)) * 10) == 0
    assert chi2([0] * 29) == 29 * 28
    return {"page_count": 56, "runes": len(joined), "pooled_chi2": round(pooled, 2),
            "sectioned_runes": 12947, "sectioned_chi2": round(section_sum, 2),
            "source_rows": len(rows), "named_classings": len(named),
            "source_gates_passed": True, "source_pooled_excluded_v_max": 168,
            "source_sectioned_excluded_v_max": 174,
            "source_sensitivity_pooled_v_max": 153,
            "source_sensitivity_sectioned_v_max": 133}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
