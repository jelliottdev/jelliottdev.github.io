"""Independent JSON-page audit of the archived two-time-pad premises."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
INDEX = {ch: pos for pos, ch in enumerate(RUNES)}


def gp(raw: str) -> list[int]:
    return [INDEX[ch] for ch in raw if ch in INDEX]


def coincidence(row: list[int]) -> float:
    counts = [0] * 29
    for value in row:
        counts[value] += 1
    return sum(n * (n - 1) for n in counts) * 29 / (len(row) * (len(row) - 1))


def all_scores(pages: dict[int, list[int]]) -> list[tuple[float, int, int, str, int]]:
    values = []
    for a, b in itertools.combinations(range(21, 55), 2):
        left, right = pages[a], pages[b]
        size = min(len(left), len(right))
        if size < 50:
            continue
        for name, factor in (("difference", -1), ("sum", 1)):
            score = coincidence([(left[i] + factor * right[i]) % 29 for i in range(size)])
            values.append((score, a, b, name, size))
    return values


def check(source_root: Path | None) -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert saved["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for source in plan["inputs"]:
        file = ROOT / source["path"]
        assert hashlib.sha256(file.read_bytes()).hexdigest() == source["sha256"], source["path"]
    if source_root is not None:
        assert source_root.is_dir()
        for source in plan["source"]["files"]:
            file = source_root / source["path"]
            assert hashlib.sha256(file.read_bytes()).hexdigest() == source["sha256"], source["path"]

    pages = {}
    for scan in range(21, 55):
        page_id = f"lp2-{scan-17:02}"
        document = json.loads((ROOT / f"data/pages/{page_id}.json").read_text(encoding="utf-8"))
        pages[scan] = gp(document["raw"])
        assert pages[scan] == gp((ROOT / f"text/{page_id}.txt").read_text(encoding="utf-8"))
    full = list(itertools.chain.from_iterable(pages[s] for s in range(21, 55)))
    assert len(full) == saved["source_stream_runes"]
    assert saved["period"]["largest_index_required"] == 2 * 6726 - 1
    assert saved["period"]["in_bounds"] is False

    for row in saved["paired_regions"]:
        a, b, size = row["source"], row["target"], row["requested_length"]
        common = min(size, max(0, len(full) - a), max(0, len(full) - b))
        assert common == row["compared_length"]
        equal = [k for k in range(common) if full[a+k] == full[b+k]]
        assert len(equal) == row["equal_runes"]
        assert row["first_difference"] == next((k for k in range(common) if k not in equal), None)
        assert row["in_bounds"] == (common == size)
        assert row["identical"] == (common == size and len(equal) == size)
    for record, a, b in ((saved["source_prefix"], pages[27], pages[44]),
                         (saved["alternative_label_prefix"],
                          gp((ROOT / "text/lp2-27.txt").read_text(encoding="utf-8")),
                          gp((ROOT / "text/lp2-44.txt").read_text(encoding="utf-8")))):
        assert len(a) == record["length_a"] and len(b) == record["length_b"]
        compared = min(len(a), len(b))
        assert record["equal_runes"] == sum(a[k] == b[k] for k in range(compared))
        assert record["first_difference"] == next((k for k in range(compared) if a[k] != b[k]), None)

    scores = all_scores(pages)
    assert len(scores) == saved["pair_screen"]["cases"] == 1122
    above = sorted((x for x in scores if x[0] > 1.15), reverse=True)
    assert len(above) == saved["pair_screen"]["hits_over_1_15"]
    for row, entry in zip(above, saved["pair_screen"]["hits"]):
        assert (row[1], row[2], row[3], row[4]) == (entry["scan_a"], entry["scan_b"], entry["operation"], entry["runes"])
        assert abs(row[0] - entry["ioc"]) < 1e-13
    assert max(scores)[0] == saved["pair_screen"]["maximum"]["ioc"]

    if source_root is not None:
        revision = plan["source"]["revision"]
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip()
        assert head == revision, (head, revision)
        source_pages = {}
        for scan in range(21, 55):
            name = f"pages/page_{scan:02}/runes.txt"
            raw = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=source_root)
            source_pages[scan] = gp(raw.decode("utf-8"))
            assert source_pages[scan] == pages[scan], name
        source_file = source_root / "tools/legacy/twotime_pad_analysis.py"
        spec = importlib.util.spec_from_file_location("wulfic_twotime_source", source_file)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source_scores = []
        for a, b in itertools.combinations(range(21, 55), 2):
            left, right = source_pages[a], source_pages[b]
            size = min(len(left), len(right))
            if size < 50:
                continue
            for name, mode in (("difference", "sub"), ("sum", "add")):
                diff = module.diff_streams(left, right, mode)
                value = module.compute_ioc(diff)
                source_scores.append((value, a, b, name, size))
        assert len(source_scores) == len(scores) == 1122
        for actual, source in zip(scores, source_scores):
            assert actual[1:] == source[1:]
            assert abs(actual[0] - source[0]) < 1e-13
        assert sum(row[0] > 1.15 for row in source_scores) == saved["pair_screen"]["hits_over_1_15"]
        assert abs(max(source_scores)[0] - saved["pair_screen"]["maximum"]["ioc"]) < 1e-13

    rng = random.Random(20261023)
    for rep in range(199):
        shuffled = {scan: page[:] for scan, page in pages.items()}
        for page in shuffled.values():
            rng.shuffle(page)
        replicate = all_scores(shuffled)
        assert abs(max(v[0] for v in replicate) - saved["null"]["maximum_ioc"][rep]) < 1e-13
        assert sum(v[0] > 1.15 for v in replicate) == saved["null"]["hits_over_1_15"][rep]
    assert saved["null"]["maxima_at_least_observed"] == sum(
        v >= saved["pair_screen"]["maximum"]["ioc"] for v in saved["null"]["maximum_ioc"])

    known = []
    for page in range(10, 14):
        document = json.loads((ROOT / f"data/pages/lp1-{page:02}.json").read_text(encoding="utf-8"))
        known.extend(gp(document["raw"]))
    length = 137
    windows = [known[k*length:(k+1)*length] for k in range(5)]
    key_rng = random.Random(3301)
    shared_key = [key_rng.randrange(29) for _ in range(length)]
    distinct_keys = [[key_rng.randrange(29) for _ in range(length)] for _ in range(5)]
    assert len(saved["plants"]) == 10
    for row in saved["plants"]:
        a, b = row["window_a"], row["window_b"]
        shared_difference = [(windows[a][k] + shared_key[k] - windows[b][k] - shared_key[k]) % 29 for k in range(length)]
        distinct_difference = [(windows[a][k] + distinct_keys[a][k] - windows[b][k] - distinct_keys[b][k]) % 29 for k in range(length)]
        assert coincidence(shared_difference) == row["same_key_difference_ioc"]
        assert coincidence(distinct_difference) == row["independent_key_difference_ioc"]
        assert row["same_key_crosses_source_screen"] == (coincidence(shared_difference) > 1.15)
    print("PASS: independent page JSON, seven premise checks, complete pair screen, 199 shuffles, 10 plants")
    if source_root is not None:
        print("PASS: all 34 page Git objects and all 1,122 source-function pair scores")
    print(f"Page-pair maximum {max(scores)[0]:.4f}; shuffled median {statistics.median(saved['null']['maximum_ioc']):.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="Optional pinned Wulfic checkout for script hash verification")
    check(parser.parse_args().source_root)
