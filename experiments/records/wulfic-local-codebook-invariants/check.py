"""Recount all LP2 repeat statistics independently from Liberpedia page text."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def rows(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def manuscript_words() -> list[list[tuple[int, ...]]]:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {entry["rune"]: entry["index"] for entry in index["alphabet"]}
    sections: list[list[tuple[int, ...]]] = [[] for _ in range(9)]
    segment, pending = 0, []

    def flush() -> None:
        if pending:
            sections[segment].append(tuple(pending))
            pending.clear()

    for page in range(56):
        data = json.loads((ROOT / f"data/pages/lp2-{page:02d}.json").read_text(encoding="utf-8"))
        for ch in data["raw"]:
            if ch in alphabet:
                pending.append(alphabet[ch])
            elif ch in "-.&$§" or (ch.isascii() and ch.isalnum()):
                flush()
                if ch == "$":
                    segment += 1
            # A slash, page break or whitespace can wrap one rune word.
    flush()
    # Nine dollars mark eight section joins plus the final end marker.
    assert segment == 9 and sum(map(len, sections)) == 2896
    assert sum(len(word) for section in sections for word in section) == 12956
    return sections


def streams_of(sections: list[list[tuple[int, ...]]]) -> list[list[int]]:
    return [[r for word in section for r in word] for section in sections]


def nonoverlap_repeats(stream: list[int], n: int) -> int:
    seen: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for i in range(len(stream) - n + 1):
        seen[tuple(stream[i:i + n])].append(i)
    total = 0
    for positions in seen.values():
        left = 0
        for j, current in enumerate(positions):
            while left < j and positions[left] <= current - n:
                left += 1
            total += left
    return total


def ngram_count(streams: list[list[int]], n: int, mode: str) -> int:
    groups = streams if mode == "sec" else [sum(streams, [])]
    return sum(nonoverlap_repeats(stream, n) for stream in groups)


def pair_count(values) -> int:
    return sum(n * (n - 1) // 2 for n in Counter(values).values())


def word_count(sections: list[list[tuple[int, ...]]], mode: str) -> int:
    groups = sections if mode == "sec" else [sum(sections, [])]
    return sum(pair_count(word for word in section if len(word) >= 2) for section in groups)


def block_count(streams: list[list[int]], n: int, mode: str, offset: int) -> int:
    groups = streams if mode == "sec" else [sum(streams, [])]
    return sum(pair_count(tuple(stream[i:i + n])
                          for i in range(offset, len(stream) - n + 1, n))
               for stream in groups)


def check() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    sections = manuscript_words()
    streams = streams_of(sections)
    aa = rows("source-stage_aa_results.tsv")
    assert {(int(r["n"]), r["mode"]) for r in aa} == {(n, mode) for n in range(3, 8)
                                                       for mode in ("sec", "cont")}
    for row in aa:
        assert ngram_count(streams, int(row["n"]), row["mode"]) == int(row["K_LP2"])
    aa_stat = {(int(r["n"]), r["mode"]): r for r in aa}
    aa_controls = rows("source-stage_aa_controls.tsv")
    assert len(aa_controls) == 260
    assert {(int(r["n"]), r["mode"], int(r["w"]), r["source"]) for r in aa_controls} == {
        (n, mode, w, source) for n in range(3, 8) for mode in ("sec", "cont")
        for w in range(13) for source in ("E", "L")}
    aa_control = {(int(r["n"]), r["mode"], int(r["w"]), r["source"]): r
                  for r in aa_controls}
    widths = rows("source-stage_aa_verdicts.tsv")
    assert {(r["mode"], int(r["w"])) for r in widths} == {
        (mode, w) for mode in ("sec", "cont") for w in range(13)}
    for row in widths:
        n_excluded = {int(n) for n in row["excluded_by_n"].split(",") if n.isdigit()}
        assert (row["verdict"] == "EXCLUDED") == bool(n_excluded)
        for n in n_excluded:
            assert row[f"n{n}"] == "EXCLUDED"
            stat = aa_stat[n, row["mode"]]
            for source in ("E", "L"):
                control = aa_control[n, row["mode"], int(row["w"]), source]
                assert int(stat["K_LP2"]) < float(control["log_lower_5sd"])
                assert float(control["log_lower_5sd"]) > int(stat["null_max"])
                assert int(control["min"]) > int(stat["null_max"])
    z = rows("source-stage_z_results.tsv")
    names = {r["cell"] for r in z}
    expected = {"Zw-sec", "Zw-all"} | {f"Zb-{n}-{mode}-{offset}"
                                            for n in range(2, 9) for mode in ("sec", "cont")
                                            for offset in range(n)}
    assert names == expected and len(z) == 72
    control = rows("source-stage_z_controls.tsv")
    assert len(control) == 144 and {(r["cell"], r["source"]) for r in control} == {
        (cell, source) for cell in expected for source in ("E", "L")}
    for row in z:
        name = row["cell"]
        if name.startswith("Zw-"):
            measured = word_count(sections, "sec" if name == "Zw-sec" else "all")
        else:
            _, n, mode, offset = name.split("-")
            measured = block_count(streams, int(n), mode, int(offset))
        assert measured == int(row["K_LP2"]), name
        if row["verdict"] == "EXCLUDED":
            assert measured < min(float(row["E_lower"]), float(row["L_lower"]))
            assert min(float(row["E_lower"]), float(row["L_lower"])) > int(row["null_max"])
            assert all(int(r["min"]) > int(row["null_max"]) for r in control if r["cell"] == name)
    # A fixed injective relabelling preserves repeated words and aligned blocks.
    toy = [[(1, 2), (3, 4), (1, 2)], [(2, 3), (1, 2)]]
    mapped = [[tuple((v + 7) % 29 for v in word) for word in sec] for sec in toy]
    assert word_count(toy, "all") == word_count(mapped, "all") == 3
    assert block_count(streams_of(toy), 2, "cont", 0) == block_count(streams_of(mapped), 2, "cont", 0)
    print("Independent page, word, n-gram, aligned-block and planted invariant checks: OK")


if __name__ == "__main__":
    check()
