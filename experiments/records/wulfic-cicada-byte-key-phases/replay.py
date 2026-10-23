"""Rebuild the exact Stage R grid with an independently implemented scorer.

Requires the pinned Wulfic checkout separately. Nothing is written into it.
Usage: python replay.py --source PATH --workers 4 --output PATH
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
import os
import pickle
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from fast import score

PIN = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
MODES = {"sub": 0, "add": 1, "beaufort": 2}
SOURCE_FILES = {
    "tools/run_stage_r.py": "ca888f78cbdf504de69ceb3309c55a064cb890fd57fb5b19c9245228f2d29eec",
    "tools/lpcore/fastdetect.py": "b98c876e2963ac257164141f0100e5cf0e034070f16628816e2544ba493530d4",
    "tools/lpcore/detect.py": "fc0f0fb715e888f9ffe0ee434f786f273a0ee939ab050d54ff4e369a8f301eeb",
    "tools/lpcore/keys.py": "551f5c0c4746c934b2317b22562fd95db969600dda2bfbe2a3ab7c359255cafc",
}
KEYS = CIPHERS = RATIO = None


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_module(source: Path):
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() != PIN:
        raise ValueError("The source checkout is not at the pinned commit")
    for path, digest in SOURCE_FILES.items():
        if sha(source / path) != digest:
            raise ValueError(f"Source file hash changed: {path}")
    source_text = subprocess.check_output(
        ["git", "show", f"HEAD:reference/community/people_2014.md"], cwd=source
    )
    if hashlib.sha256(source_text).hexdigest() != "d2e546fd4e5505a3a3aa45dc6a453fd181b2d0a4f3295361f0e754e3a40ae56b":
        raise ValueError("Pinned community source hash changed")
    sys.path.insert(0, str(source))
    r = importlib.import_module("tools.run_stage_r")
    return r, source_text


def prepare(source: Path, path: Path) -> dict:
    r, source_text = source_module(source)
    from tools.lpcore import detect, keys, stats
    from tools.lpcore.corpus import load_corpus
    from tools.lpcore.verify import load_translation
    corpus = load_corpus()
    with tempfile.TemporaryDirectory() as directory:
        # Sparse checkout omits a tracked Markdown witness. Restore into a
        # temporary file only, never modify the pinned checkout.
        onion = Path(directory) / "people_2014.md"
        onion.write_bytes(source_text)
        r.ONION_2_HEX_SOURCE = onion
        family = r.family(corpus)
    plain = [rune for word in keys.solved_plaintext_words(corpus, load_translation()) for rune in word]
    q = detect.unigram(plain)
    ratio = np.asarray(detect.emission_ratios(q, detect.EPS), dtype=np.float64)
    segments = [str(s) for s in stats.UNSOLVED_SEGMENTS] + ["7-15"]
    ciphers = {str(s): np.asarray(corpus.segment_runes(s), dtype=np.int64) for s in stats.UNSOLVED_SEGMENTS}
    ciphers["7-15"] = np.concatenate([ciphers[str(s)] for s in stats.UNSOLVED_SEGMENTS])
    expected_lengths = [729,1145,1729,9,1894,1021,1524,1589,3316,12956]
    if [len(ciphers[s]) for s in segments] != expected_lengths:
        raise ValueError("Source segment lengths differ from the frozen plan")
    profile = {
        "keys": {name: np.asarray(value, dtype=np.int64) for name, value in family.items()},
        "ciphers": ciphers,
        "ratio": ratio,
        "q": q,
        "plain": plain,
        "segments": segments,
        "by_cost": sorted(family, key=lambda name: -len(family[name])),
    }
    if len(family) != 50:
        raise ValueError("Expected 50 mapped source streams")
    with path.open("wb") as output:
        pickle.dump(profile, output, protocol=4)
    return profile


def init_worker(path: str):
    global KEYS, CIPHERS, RATIO
    with Path(path).open("rb") as handle:
        profile = pickle.load(handle)
    KEYS, CIPHERS, RATIO = profile["keys"], profile["ciphers"], profile["ratio"]


def one_group(arg):
    name, segment = arg
    key = KEYS[name]
    cipher = CIPHERS[segment]
    alignment = "continuous" if segment == "7-15" else "per-section"
    rows = []
    for mode, number in MODES.items():
        for shift in range(29):
            value = score(cipher, key, RATIO, number, shift)
            rows.append((name, alignment, segment, mode, shift, len(cipher), value))
    return rows


def check_parity(r, profile):
    # Source and independent implementation on all source modes; short,
    # medium and 58-kb key streams; first/last shifts and joined alignment.
    names = profile["by_cost"]
    selected = [names[0], names[3], names[10], names[-1]]
    cells = []
    for name in selected:
        key = profile["keys"][name]
        for segment in ("10", "7", "7-15"):
            cipher = profile["ciphers"][segment]
            for mode in MODES:
                for shift in (0, 13, 28):
                    mine = score(cipher, key, profile["ratio"], MODES[mode], shift)
                    theirs = r.score_cyclic(cipher.tolist(), key.tolist(), profile["q"], mode, shift)
                    if abs(mine - theirs) > 1e-8:
                        raise AssertionError((name, segment, mode, shift, mine, theirs))
                    cells.append((name, segment, mode, shift, abs(mine - theirs)))
    return cells


def compare_rows(actual: Path, expected: Path, count: int):
    with actual.open("r", encoding="utf-8", newline="") as ah, expected.open("r", encoding="utf-8", newline="") as eh:
        a, e = list(csv.DictReader(ah, delimiter="\t")), list(csv.DictReader(eh, delimiter="\t"))
    if len(a) != len(e) or len(a) != count:
        raise AssertionError(("row_count", len(a), len(e), count))
    diffs = []
    for i, (row, prior) in enumerate(zip(a, e)):
        if row != prior:
            diffs.append((i, row, prior))
            if len(diffs) >= 5:
                break
    if diffs:
        raise AssertionError(("source_row_mismatch", diffs))
    return a


def pinned_table(source: Path, name: str, destination: Path, digest: str):
    data = subprocess.check_output(["git", "show", f"HEAD:reference/findings/{name}"], cwd=source)
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Pinned result table hash changed: {name}")
    destination.write_bytes(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not 1 <= args.workers <= 8:
        p.error("workers must be from 1 to 8")
    args.output.mkdir(parents=True, exist_ok=True)
    r, _ = source_module(args.source)
    profile_path = args.output / "source-profile.pickle"
    profile = prepare(args.source, profile_path)
    parity = check_parity(r, profile)
    print(f"Pinned-source numerical parity: {len(parity)} cells; largest absolute delta {max(row[-1] for row in parity):.3g}", flush=True)
    control_path = args.output / "stage_r_controls.tsv"
    # Preserve the source's control generator and RNG call sequence. Only its
    # scorer is substituted, after independent source-parity validation.
    r.score_cyclic = lambda cipher, key, q, mode, shift: score(
        np.asarray(cipher, dtype=np.int64), np.asarray(key, dtype=np.int64),
        profile["ratio"], MODES[mode], shift
    )
    controls = r.controls({k: v.tolist() for k, v in profile["keys"].items()}, profile["q"], profile["plain"])
    r.write_controls(controls, control_path)
    expected = args.output / "source-stage_r_controls.tsv"
    pinned_table(args.source, "stage_r_controls.tsv", expected,
                 "e302f6009e63ba17de950ad396be2001a2c922d047e0da83b22990efefb6a29b")
    compare_rows(control_path, expected, 200)
    if min(row[4] for row in controls) < 30 or max(row[5] for row in controls) >= 30:
        raise AssertionError("Planted control gate failed")
    print("All 200 control rows agree with pinned source table; planted gate passes", flush=True)
    groups = [(name, segment) for name in profile["by_cost"] for segment in profile["segments"]]
    candidate_path = args.output / "stage_r_candidates.tsv"
    header = "key\talignment\tsegment\tmode\tshift\trunes\tlog_lr_nats\n"
    with candidate_path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(header)
        with ProcessPoolExecutor(max_workers=args.workers, initializer=init_worker, initargs=(str(profile_path),)) as pool:
            for i, rows in enumerate(pool.map(one_group, groups, chunksize=1), 1):
                for name, alignment, segment, mode, shift, n, value in rows:
                    output.write(f"{name}\t{alignment}\t{segment}\t{mode}\t{shift}\t{n}\t{value:.2f}\n")
                if i % 20 == 0:
                    output.flush()
                    print(f"Scored {i}/500 source groups", flush=True)
    expected_candidates = args.output / "source-stage_r_candidates.tsv"
    pinned_table(args.source, "stage_r_candidates.tsv", expected_candidates,
                 "7636b6e93acc24f221ce5e7ef70419a17ff238c3a0d94becb69ece22707d1949")
    rows = compare_rows(candidate_path, expected_candidates, 43500)
    report = {
        "candidate_count": len(rows),
        "control_count": len(controls),
        "parity_cells": len(parity),
        "parity_max_abs_delta": max(row[-1] for row in parity),
        "candidate_exact_tsv_sha256": sha(candidate_path),
        "control_exact_tsv_sha256": sha(control_path),
        "candidate_pass_count": sum(float(row["log_lr_nats"]) >= 30 for row in rows),
        "candidate_max_rounded": max(float(row["log_lr_nats"]) for row in rows),
        "best_non_title_rounded": max(float(row["log_lr_nats"]) for row in rows if row["segment"] != "10"),
        "joined_max_rounded": max(float(row["log_lr_nats"]) for row in rows if row["segment"] == "7-15"),
        "title_runes": len(profile["ciphers"]["10"]),
        "title_settings": sum(row["segment"] == "10" for row in rows),
        "title_absolute_score_bound": len(profile["ciphers"]["10"]) * math.log(max(profile["ratio"])),
        "max_emission_ratio": float(max(profile["ratio"])),
        "positive_min": min(row[4] for row in controls),
        "negative_max": max(row[5] for row in controls),
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
