"""Control-only prototype for the pinned LiberPrayground trigram display."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = None
PLAN = json.loads((HERE / "precontrol-plan.json").read_text(encoding="utf-8"))


def checked(path, expected):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, path
    return raw


def source_blob(name):
    return subprocess.check_output(["git", "show", "HEAD:" + name], cwd=SOURCE)


def setup_source(temp):
    files = ["LP/Alphabet.py", "LP/Rune.py", "LP/RuneText.py", "LP/NGrams.py", "LP/LPath.py", "LP/FailedAttempts.py", "data/p-3gram.txt"]
    for name in files:
        path = temp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source_blob(name))
    assert hashlib.sha256((temp / "LP/FailedAttempts.py").read_bytes()).hexdigest() == PLAN["source_sha256"]
    assert hashlib.sha256((temp / "data/p-3gram.txt").read_bytes()).hexdigest() == PLAN["trigram_file"]["sha256"]
    oldcwd = Path.cwd()
    os.chdir(temp)
    sys.path.insert(0, str(temp / "LP"))
    try:
        from FailedAttempts import NGramShifter
        from Alphabet import RUNES, rune_map
        from RuneText import RuneText
        yield NGramShifter(), RUNES, rune_map, RuneText
    finally:
        sys.path.remove(str(temp / "LP"))
        os.chdir(oldcwd)


def score_table():
    p = PROJECT / PLAN["scorer"]["path"]
    raw = checked(p, PLAN["scorer"]["sha256"]).decode("utf-8")
    freq = {w: int(n) for w, n in (line.split() for line in raw.splitlines())}
    denom = sum(freq.values())
    floor = PLAN["scorer"]["floor_count"]
    return {w: math.log10(n / denom) for w, n in freq.items()}, math.log10(floor / denom)


def rows(heatmap, rune_map, model, floor, plain=None, phase=0):
    output = []
    for rank in range(29):
        chunks = []
        exact = 0
        visible = 0
        for i, variants in enumerate(heatmap):
            shift, count, runes = variants[rank]
            if count:
                chunks.append("".join(rune_map[c] for c in runes))
                visible += 3
                if plain is not None:
                    exact += sum(runes[j] == plain[phase + i * 3 + j] for j in range(3))
            else:
                chunks.append("")
        grams = []
        fragment = ""
        for chunk in chunks + [""]:
            if chunk:
                fragment += chunk
            else:
                grams.extend(fragment[i:i + 4] for i in range(len(fragment) - 3))
                fragment = ""
        scored = len(grams)
        candidate = {
            "rank": rank,
            "quadgrams": scored,
            "visible_runes": visible,
            "exact_runes": exact,
            "complete_runes": len(heatmap) * 3,
            "mean_quadgram_log10": sum(model.get(g, floor) for g in grams) / scored if scored else None,
        }
        if plain is not None:
            candidate["visible_latin_preview"] = "".join(chunk if chunk else " · " for chunk in chunks)[:120]
            candidate["known_latin_preview"] = "".join(rune_map[c] for c in plain[phase:phase + len(heatmap) * 3])[:120]
        output.append(candidate)
    return output


def scan(pages, shifter, RUNES, rune_map, RuneText, model, floor, keep_all=False):
    best = None
    all_top = []
    for page, plain in pages:
        cipher = [(x + 7) % 29 for x in plain]
        for phase in range(3):
            heatmap = shifter.ngram_probability_heatmap(RuneText(cipher[phase:]))
            if keep_all:
                for block_idx, source_rows in enumerate(heatmap):
                    block = cipher[phase + 3 * block_idx:phase + 3 * block_idx + 3]
                    direct = []
                    for shift in range(29):
                        runes = "".join(RUNES[(index - shift) % 29] for index in block)
                        direct.append((shift, shifter.prob.get(runes, 0), runes))
                    direct.sort(key=lambda row: -row[1])
                    assert direct == source_rows, (page, phase, block_idx)
            candidates = rows(heatmap, rune_map, model, floor, plain=[RUNES[x] for x in plain] if keep_all else None, phase=phase)
            for cand in candidates:
                if cand["quadgrams"] < 100:
                    continue
                cand = {"page": page, "phase": phase, **cand}
                if best is None or cand["mean_quadgram_log10"] > best["mean_quadgram_log10"]:
                    best = cand
            if keep_all:
                top = {"page": page, "phase": phase, **candidates[0]}
                top["rank0_exact_fraction"] = top["exact_runes"] / top["complete_runes"]
                ties = [sum(v[1] == variants[0][1] for v in variants) for variants in heatmap]
                top["top_shift_tie_blocks"] = sum(n > 1 for n in ties)
                all_top.append(top)
    return best, all_top


def main():
    global SOURCE
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True, help="separate checkout of pinned LiberPrayground revision")
    ap.add_argument("--check", action="store_true", help="recompute without writing and compare the saved receipt")
    args = ap.parse_args()
    SOURCE = args.source_root.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == PLAN["source_commit"]
    readings = json.loads(checked(PROJECT / PLAN["known_readings"]["path"], PLAN["known_readings"]["sha256"]))
    pages = [(p["page"], p["rune_indices"]) for c in readings["controls"] for p in c["decoded_pages"]]
    assert len(pages) == 17 and all(all(0 <= i < 29 for i in nums) for _, nums in pages)
    model, floor = score_table()
    with tempfile.TemporaryDirectory(prefix="relikd-trigram-control-") as name:
        source = setup_source(Path(name))
        shifter, RUNES, rune_map, RuneText = next(source)
        # All 29 source rows of a short shifted known string must match direct GP arithmetic.
        plain = "ᚪᚾᛞ"
        cipher = [((RUNES.index(c) + 7) % 29) for c in plain]
        got = shifter.ngram_probability_heatmap(RuneText(cipher))
        f = shifter.prob
        expect = sorted(((s, f.get("".join(RUNES[(x - s) % 29] for x in cipher), 0), "".join(RUNES[(x - s) % 29] for x in cipher)) for s in range(29)), key=lambda row: -row[1])
        assert got == [expect]
        observed, top = scan(pages, shifter, RUNES, rune_map, RuneText, model, floor, True)
        rng = random.Random(20261023)
        nulls = []
        for trial in range(49):
            shuffled = []
            for page, nums in pages:
                array = nums[:]
                rng.shuffle(array)
                shuffled.append((page, array))
            winner, _ = scan(shuffled, shifter, RUNES, rune_map, RuneText, model, floor)
            nulls.append({"trial": trial, "max": winner})
        out = {
            "scope": "known-page controls only; no LP2 target was evaluated",
            "source_parity": "Original pinned NGramShifter result equals independent 29-shift enumeration on the planted top trigram and on every block of all 51 known-page phase displays",
            "known_page_count": len(pages),
            "plant_shift": 7,
            "selected_known_max": observed,
            "rank0_by_page_phase": top,
            "null_maxima": nulls,
            "null_at_least_selected_known": sum(x["max"]["mean_quadgram_log10"] >= observed["mean_quadgram_log10"] for x in nulls),
        }
        if args.check:
            saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
            assert out == saved, "recomputed source receipt differs"
        else:
            (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"selected": observed, "null_trials": len(nulls), "null_at_least": out["null_at_least_selected_known"], "rank0_minmax": [min(x["rank0_exact_fraction"] for x in top), max(x["rank0_exact_fraction"] for x in top)]}, indent=2))
        try:
            next(source)
        except StopIteration:
            pass


if __name__ == "__main__":
    main()
