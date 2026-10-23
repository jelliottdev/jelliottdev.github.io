"""Two documented LP1 repeating keys on LP2-53's 51 red runes."""
import argparse
import hashlib
import json
from pathlib import Path
import random

from controls import HERE, ROOT, PLAN, setup, verified


def produce():
    gate = json.loads((HERE / "controls.json").read_text(encoding="utf-8"))
    if not gate["passed"] or gate["good_originals"] < 8 or gate["top_rank_plants"] < 8:
        raise ValueError("Pre-manuscript score gate failed")
    verified(ROOT / "images/lp2-53.jpg", PLAN["source_image_sha256"])
    page = json.loads(verified(ROOT / "data/pages/lp2-53.json", PLAN["source_page_json_sha256"]))
    alphabet = json.loads(verified(ROOT / "data/index.json", PLAN["alphabet_sha256"]))["alphabet"]
    rune_to_index = {r["rune"]: i for i, r in enumerate(alphabet)}
    if page["rune_count"] != 179 or len(page["lines"]) != 9:
        raise ValueError("Unexpected page transcription")
    line_indices = [[rune_to_index[c] for c in line["raw"] if c in rune_to_index] for line in page["lines"]]
    assert [len(row) for row in line_indices] == [22, 22, 20, 23, 23, 19, 24, 22, 4]
    red = line_indices[5][-1:] + [v for line in line_indices[6:] for v in line]
    assert len(red) == PLAN["target_length"] == 51
    assert sum(map(len, line_indices[:5])) + len(line_indices[5]) - 1 == PLAN["target_rune_start_zero_based"]
    red_raw = page["lines"][5]["raw"].split(".")[-1] + "".join(line["raw"] for line in page["lines"][6:])
    lengths = [sum(ch in rune_to_index for ch in word) for word in red_raw.replace("/", "").split("-")]
    lengths = [n for n in lengths if n]
    assert lengths == PLAN["word_lengths"]

    keys, score, candidates = setup()
    ranked = sorted(candidates(red), key=lambda row: (-row[1], row[0]))
    if len(ranked) != 2 * sum(len(k["indices"]) for k in keys):
        raise ValueError("Wrong candidate count")
    best = ranked[0][1]
    null_maxima = []
    for repeat in range(999):
        shuffled = red.copy()
        random.Random(PLAN["control_seed"] + 100000 + repeat).shuffle(shuffled)
        null_maxima.append(max(row[1] for row in candidates(shuffled)))
    latin = [r["latin"] for r in alphabet]
    cases = [{"key": label[0], "phase": label[1], "sign": label[2], "score": value,
              "output": "".join(latin[i] for i in plain),
              "output_indices_sha256": hashlib.sha256(bytes(plain)).hexdigest()}
             for label, value, plain in ranked]
    return {"schema": "liberpedia-lp2-53-red-known-keys-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "controls_sha256": hashlib.sha256((HERE / "controls.json").read_bytes()).hexdigest(),
            "red_rune_start_zero_based": 128, "red_rune_end_exclusive": 179,
            "red_indices": red, "word_lengths": lengths,
            "case_count": len(cases), "cases": cases,
            "best_score": best, "score_threshold": PLAN["score_threshold"],
            "null_maxima": null_maxima,
            "null_at_least_best": sum(x >= best for x in null_maxima),
            "empirical_family_tail_fraction": (1 + sum(x >= best for x in null_maxima)) / 1000,
            "passing_fixed_threshold": sum(x["score"] >= PLAN["score_threshold"] for x in cases)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = produce()
    path = HERE / "results.json"
    if args.check:
        if result != json.loads(path.read_text(encoding="utf-8")):
            raise SystemExit("Computed result differs from saved result")
    else:
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: result[k] for k in ("case_count", "best_score", "passing_fixed_threshold", "null_at_least_best", "empirical_family_tail_fraction")}))
