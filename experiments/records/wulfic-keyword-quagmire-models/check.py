"""Independent site input and complete source-decision audit for Stage V."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FAMILIES = ("English runes", "English prime values", "English Latin A-Z", "decimal digits", "hex digits", "letters A-Z")
MEMBERS = 68 ** 3


def site_counts() -> list[int]:
    alphabet = {e["rune"]: e["index"] for e in json.loads(
        (ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    assert sorted(alphabet.values()) == list(range(29))
    counts = Counter()
    for page in range(56):
        raw = json.loads((ROOT / f"data/pages/lp2-{page:02d}.json").read_text(encoding="utf-8"))["raw"]
        counts.update(alphabet[glyph] for glyph in raw if glyph in alphabet)
    return [counts[i] for i in range(29)]


def row(rows: list[dict[str, str]], kind: str, family: str) -> dict[str, str]:
    selected = [r for r in rows if r["kind"] == kind and r["family"] == family]
    assert len(selected) == 1, (kind, family)
    return selected[0]


def verify() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    observed = site_counts()
    assert observed == plan["observed_counts_gp29"] and sum(observed) == 12956
    with (HERE / "source-stage_v_results.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 10357
    kinds = Counter(r["kind"] for r in rows)
    assert kinds == {"alphabets": 1, "gate_G1": 6, "gate_G2": 6, "identity": 6, "lp2": 6,
                     "member": 10332}
    assert int(row(rows, "alphabets", "-")["size"]) == 68
    members_by_family = defaultdict(list)
    for item in rows:
        if item["kind"] == "member":
            members_by_family[item["family"]].append(item)
    summaries = []
    for family in FAMILIES:
        calibration = row(rows, "gate_G1", family)
        assert int(calibration["size"]) == 50
        match = re.fullmatch(r"worst own-member best LLR ([+-]\d+\.\d+) ok", calibration["detail"])
        assert match and float(match[1]) > -10
        power = row(rows, "gate_G2", family)
        assert int(power["size"]) == 20
        match = re.fullmatch(r"testable (\d+) / (\d+)", power["detail"])
        assert match and int(match[2]) == MEMBERS
        testable = int(match[1])
        assert 0 <= testable <= MEMBERS
        source = row(rows, "lp2", family)
        assert int(source["size"]) == MEMBERS
        pattern = (r"excluded (\d+); not excluded, testable (\d+); "
                   r"untestable, not excluded (\d+); leads (\d+); max ([+-]\d+\.\d+)")
        match = re.fullmatch(pattern, source["detail"])
        assert match, (family, source["detail"])
        raw_excluded, powered_open, open_unpowered, leads = map(int, match.groups()[:4])
        max_llr = float(match[5])
        assert raw_excluded + powered_open + open_unpowered == MEMBERS
        assert 0 <= powered_open <= testable
        assert leads == 0 and max_llr < 10
        powered_excluded = testable - powered_open
        untestable = MEMBERS - testable
        # The source lists every powered survivor and every lead. There are
        # no leads, so all 10,332 listed members must be powered survivors.
        listed = members_by_family[family]
        assert len(listed) == powered_open
        for item in listed:
            detail = re.fullmatch(r"best LLR ([+-]\d+\.\d+); testable", item["detail"])
            assert detail and -10 < float(detail[1]) < 10
        summaries.append({"family": family, "powered_excluded": powered_excluded,
                          "powered_open": powered_open, "untestable": untestable,
                          "raw_excluded": raw_excluded, "max_llr": max_llr})
    assert sum(r["powered_open"] for r in summaries) == kinds["member"]
    assert sum(r["powered_excluded"] + r["powered_open"] + r["untestable"] for r in summaries) == 6 * MEMBERS
    return {"source_rows": len(rows), "keyword_alphabets": 68, "families": len(FAMILIES),
            "source_members_per_family": MEMBERS, "source_gate_G1_passed": True,
            "source_leads": 0, "observed_runes": sum(observed), "family_summaries": summaries}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
