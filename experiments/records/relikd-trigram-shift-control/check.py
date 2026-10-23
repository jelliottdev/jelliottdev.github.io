"""Independent arithmetic and complete-selection check; imports no upstream code or run.py."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "precontrol-plan.json").read_text(encoding="utf-8"))
SAVED = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LATIN = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA")


def checked(path, digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, path
    return raw


def same(got, saved):
    if isinstance(saved, float):
        assert math.isclose(got, saved, abs_tol=2e-13), (got, saved)
    elif isinstance(saved, dict):
        assert got.keys() == saved.keys()
        for key in saved:
            same(got[key], saved[key])
    elif isinstance(saved, list):
        assert len(got) == len(saved)
        for x, y in zip(got, saved):
            same(x, y)
    else:
        assert got == saved, (got, saved)


def evaluate(pages, frequencies, weights, floor, full):
    winner = None
    top_rows = []
    for page, actual in pages:
        shifted = [(x + 7) % 29 for x in actual]
        for phase in range(3):
            blocks = [shifted[i:i + 3] for i in range(phase, len(shifted) - 2, 3)]
            options = []
            for block in blocks:
                vals = []
                for shift in range(29):
                    decoded = tuple((x - shift) % 29 for x in block)
                    vals.append((shift, frequencies.get("".join(RUNES[x] for x in decoded), 0), decoded))
                # Python's stable sort preserves source's shift order on ties.
                options.append(sorted(vals, key=lambda row: -row[1]))
            if full:
                ties = sum(sum(row[1] == opts[0][1] for row in opts) > 1 for opts in options)
            for rank in range(29):
                fragments = []
                exact = visible = 0
                for pos, opts in enumerate(options):
                    _shift, count, decoded = opts[rank]
                    if count:
                        visible += 3
                        fragments.append("".join(LATIN[x] for x in decoded))
                        if full:
                            exact += sum(decoded[j] == actual[phase + pos * 3 + j] for j in range(3))
                    else:
                        fragments.append("")
                # Empty source cells interrupt runs of Latin quadgrams.
                grams = []
                run = ""
                for frag in fragments + [""]:
                    if frag:
                        run += frag
                    else:
                        grams.extend(run[i:i + 4] for i in range(max(0, len(run) - 3)))
                        run = ""
                q = len(grams)
                row = {
                    "rank": rank,
                    "quadgrams": q,
                    "visible_runes": visible,
                    "exact_runes": exact,
                    "complete_runes": len(blocks) * 3,
                    "mean_quadgram_log10": sum(weights.get(g, floor) for g in grams) / q if q else None,
                }
                if full:
                    row["visible_latin_preview"] = "".join(x if x else " · " for x in fragments)[:120]
                    row["known_latin_preview"] = "".join(LATIN[x] for x in actual[phase:phase + len(blocks) * 3])[:120]
                if q >= 100:
                    cand = {"page": page, "phase": phase, **row}
                    if winner is None or cand["mean_quadgram_log10"] > winner["mean_quadgram_log10"]:
                        winner = cand
                if full and rank == 0:
                    top_rows.append({"page": page, "phase": phase, **row,
                                     "rank0_exact_fraction": exact / (len(blocks) * 3),
                                     "top_shift_tie_blocks": ties})
    return winner, top_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True)
    args = ap.parse_args()
    src = args.source_root.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=src, text=True).strip() == PLAN["source_commit"]
    def blob(path, digest):
        raw = subprocess.check_output(["git", "show", "HEAD:" + path], cwd=src)
        assert hashlib.sha256(raw).hexdigest() == digest
        return raw
    gram_raw = blob(PLAN["trigram_file"]["path"], PLAN["trigram_file"]["sha256"])
    blob("LP/FailedAttempts.py", PLAN["source_sha256"])
    frequencies = {w: int(n) for w, n in (line.split() for line in gram_raw.decode("utf-8").splitlines())}
    readings = json.loads(checked(ROOT / PLAN["known_readings"]["path"], PLAN["known_readings"]["sha256"]))
    pages = [(p["page"], p["rune_indices"]) for c in readings["controls"] for p in c["decoded_pages"]]
    assert len(pages) == 17 and len({p for p, _ in pages}) == 17
    raw = checked(ROOT / PLAN["scorer"]["path"], PLAN["scorer"]["sha256"]).decode("utf-8")
    counts = {w: int(n) for w, n in (line.split() for line in raw.splitlines())}
    total = sum(counts.values())
    weights = {w: math.log10(n / total) for w, n in counts.items()}
    floor = math.log10(PLAN["scorer"]["floor_count"] / total)
    # Check source table and stable tie behavior on a top-trigram plant.
    triple = tuple(RUNES.index(x) for x in "ᚪᚾᛞ")
    planted = tuple((x + 7) % 29 for x in triple)
    ranked = sorted(range(29), key=lambda s: -frequencies.get("".join(RUNES[(x - s) % 29] for x in planted), 0))
    assert ranked[0] == 7
    observed, top = evaluate(pages, frequencies, weights, floor, True)
    same(observed, SAVED["selected_known_max"])
    same(top, SAVED["rank0_by_page_phase"])
    rng = random.Random(20261023)
    trial_rows = []
    for trial in range(49):
        shuffled = []
        for page, actual in pages:
            arr = actual[:]
            rng.shuffle(arr)
            shuffled.append((page, arr))
        winner, _ = evaluate(shuffled, frequencies, weights, floor, False)
        trial_rows.append({"trial": trial, "max": winner})
    same(trial_rows, SAVED["null_maxima"])
    exceeds = sum(x["max"]["mean_quadgram_log10"] >= observed["mean_quadgram_log10"] for x in trial_rows)
    assert exceeds == SAVED["null_at_least_selected_known"] == 0
    assert observed["exact_runes"] == 129 and observed["complete_runes"] == 207
    assert observed["exact_runes"] / observed["complete_runes"] < 0.70
    print("PASS: 51 complete rank-zero displays, selected max, all 49 shared whole-search maxima, gate failure")


if __name__ == "__main__":
    main()
