"""Full-page search for two documented LP1 repeating keys; standard-library only."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
INPUTS = {row["path"]: row["sha256"] for row in PLAN["inputs"]}


def source(path):
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUTS[rel]:
        raise ValueError(f"Source changed: {rel}")
    return raw


def setup():
    alphabet = json.loads(source(ROOT / "data/index.json"))["alphabet"]
    lookup = {item["rune"]: i for i, item in enumerate(alphabet)}
    latin = [item["latin"] for item in alphabet]
    known = json.loads(source(ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json"))
    keys = [(row["id"], row["indices"]) for row in known["keys"] if row["id"] in PLAN["keys"]]
    if [name for name, _ in keys] != PLAN["keys"] or [len(v) for _, v in keys] != [8, 13]:
        raise ValueError("Known key source changed")
    lines = source(ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()
    counts = {g: int(n) for g, n in (line.split() for line in lines)}
    total = sum(counts.values())
    log_total = math.log10(total)
    weights = {g: math.log10(n) - log_total for g, n in counts.items()}
    floor = math.log10(0.01) - log_total
    settings = [(name, phase, sign, values) for name, values in keys for phase in range(len(values)) for sign in (-1, 1)]
    assert len(settings) == 42

    def score(plain):
        text = "".join(latin[x] for x in plain)
        return sum(weights.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)

    def decode(cipher, setting):
        _, phase, sign, values = setting
        return [(c + sign * values[(i + phase) % len(values)]) % 29 for i, c in enumerate(cipher)]

    return lookup, latin, settings, score, decode


def controls(settings, score, decode):
    rows = []
    for number, name in enumerate(("warning", "welcome", "some-wisdom", "first-koan", "second-koan",
                                   "loss-of-divinity", "instruction", "lp2-56", "lp2-57")):
        raw = source(ROOT / f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = [int(row["output_index"]) for row in csv.DictReader(raw.splitlines())][:PLAN["control_length"]]
        assert len(plain) == PLAN["control_length"]
        direct = score(plain)
        shuffles_below = 0
        for rep in range(PLAN["control_replicates"]):
            shuffled = plain.copy()
            random.Random(PLAN["control_seed"] + 1000 * number + rep).shuffle(shuffled)
            shuffles_below += score(shuffled) < direct
        setting = settings[(number * 7 + 3) % len(settings)]
        key = setting[3]
        cipher = [(p - setting[2] * key[(i + setting[1]) % len(key)]) % 29 for i, p in enumerate(plain)]
        scores = sorted(((score(decode(cipher, item)), item[:3]) for item in settings), reverse=True)
        true_rank = next(i + 1 for i, (_, label) in enumerate(scores) if label == setting[:3])
        assert decode(cipher, setting) == plain
        rows.append({"reading": name, "source_score": direct, "shuffles_below": shuffles_below,
                     "planted_setting": list(setting[:3]), "planted_true_rank": true_rank})
    good = sum(x["source_score"] >= PLAN["score_threshold"] and x["shuffles_below"] >= 198 for x in rows)
    plants = sum(x["planted_true_rank"] == 1 for x in rows)
    return {"rows": rows, "good_originals": good, "top_rank_plants": plants, "passed": good >= 8 and plants >= 8}


def produce(control_only=False):
    lookup, latin, settings, score, decode = setup()
    gate = controls(settings, score, decode)
    if control_only:
        return gate
    if not gate["passed"]:
        raise ValueError("Predeclared control gate failed; manuscript results not scored")
    pages = []
    for name in PLAN["pages"]:
        data = json.loads(source(ROOT / f"data/pages/{name}.json"))
        cipher = [lookup[r] for line in data["lines"] for r in line["raw"] if r in lookup]
        assert len(cipher) == data["rune_count"] and len(cipher) >= 66
        pages.append((name, cipher))
    empty = json.loads(source(ROOT / "data/pages/lp2-50.json"))
    assert empty["rune_count"] == 0 and len(pages) == 55
    cases = []
    for page, cipher in pages:
        for setting in settings:
            plain = decode(cipher, setting)
            cases.append({"page": page, "key": setting[0], "phase": setting[1], "sign": setting[2],
                          "runes": len(plain), "score": score(plain),
                          "indices_sha256": hashlib.sha256(bytes(plain)).hexdigest()})
    cases.sort(key=lambda x: (-x["score"], x["page"], x["key"], x["phase"], x["sign"]))
    maxima = []
    for rep in range(PLAN["null_replicates"]):
        best = -math.inf
        for page_number, (_, cipher) in enumerate(pages):
            shuffled = cipher.copy()
            random.Random(PLAN["null_seed"] + rep * 1000 + page_number).shuffle(shuffled)
            for setting in settings:
                value = score(decode(shuffled, setting))
                if value > best:
                    best = value
        maxima.append(best)
    best = cases[0]["score"]
    return {"schema": "liberpedia-wholepage-known-keys-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "control_gate": gate, "page_count": len(pages), "case_count": len(cases),
            "cases": cases, "best_score": best,
            "threshold_passes": sum(x["score"] >= PLAN["score_threshold"] for x in cases),
            "null_maxima": maxima, "null_at_least_best": sum(x >= best for x in maxima),
            "empirical_global_tail": (1 + sum(x >= best for x in maxima)) / (len(maxima) + 1)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    value = produce(args.controls_only)
    if args.controls_only:
        print(json.dumps({k: value[k] for k in ("good_originals", "top_rank_plants", "passed")}))
    elif args.check:
        assert value == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("Full-page search and global null match saved results")
    else:
        (HERE / "results.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: value[k] for k in ("case_count", "best_score", "threshold_passes", "null_at_least_best", "empirical_global_tail")}))
