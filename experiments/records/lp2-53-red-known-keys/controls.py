"""Pre-manuscript quality gate for a 51-rune known-key score search."""
import csv
import hashlib
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def verified(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Input changed: {path}")
    return raw


def load_model():
    path = ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt"
    lines = verified(path, PLAN["quadgram_model_sha256"]).decode("ascii").splitlines()
    counts = {gram: int(count) for gram, count in (line.split() for line in lines)}
    total = sum(counts.values())
    return {gram: math.log10(n / total) for gram, n in counts.items()}, math.log10(0.01 / total)


def setup():
    alphabet = json.loads(verified(ROOT / "data/index.json", PLAN["alphabet_sha256"]))["alphabet"]
    latin = [x["latin"] for x in alphabet]
    keys = json.loads(verified(ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json", PLAN["known_keys_plan_sha256"]))["keys"]
    keys = [x for x in keys if x["id"] in PLAN["key_ids"]]
    if len(keys) != 2 or [len(x["indices"]) for x in keys] != [8, 13]:
        raise ValueError("Unexpected known keys")
    grams, floor = load_model()

    def score(indices):
        text = "".join(latin[x] for x in indices)
        return sum(grams.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)

    def candidates(cipher):
        for key in keys:
            values = key["indices"]
            for phase in range(len(values)):
                for sign in PLAN["signs"]:
                    plain = [(c + sign * values[(i + phase) % len(values)]) % 29 for i, c in enumerate(cipher)]
                    yield (key["id"], phase, sign), score(plain), plain

    return keys, score, candidates


def controls():
    keys, score, candidates = setup()
    rows = []
    for number, (name, expected_sha) in enumerate(PLAN["control_readings"]):
        path = ROOT / "exports/readings" / f"{name}.csv"
        decoded = verified(path, expected_sha).decode("utf-8-sig")
        source = [int(r["output_index"]) for r in csv.DictReader(decoded.splitlines())][:51]
        if len(source) != 51:
            raise ValueError(f"Short reading: {name}")
        original = score(source)
        shuffles = []
        for repeat in range(PLAN["control_shuffle_replicates"]):
            copy = source.copy()
            random.Random(PLAN["control_seed"] + 1000 * number + repeat).shuffle(copy)
            shuffles.append(score(copy))
        key = keys[number % 2]
        phase = (7 * number + 3) % len(key["indices"])
        sign = PLAN["signs"][number % 2]
        cipher = [(p - sign * key["indices"][(i + phase) % len(key["indices"])]) % 29 for i, p in enumerate(source)]
        ranked = sorted(candidates(cipher), key=lambda row: (-row[1], row[0]))
        true_label = (key["id"], phase, sign)
        true_rank = next(i + 1 for i, item in enumerate(ranked) if item[0] == true_label)
        assert ranked[true_rank - 1][2] == source
        rows.append({"reading": name, "source_score": original, "shuffles_below": sum(s < original for s in shuffles),
                     "shuffle_count": len(shuffles), "shuffled_max": max(shuffles), "planted_true_rank": true_rank,
                     "planted_top_score": ranked[0][1], "planted_true_score": ranked[true_rank - 1][1]})
    good_originals = sum(row["source_score"] >= PLAN["score_threshold"] and row["shuffles_below"] >= 198 for row in rows)
    recovered_plants = sum(row["planted_true_rank"] == 1 for row in rows)
    return {"schema": "liberpedia-lp2-53-red-controls-v1", "rows": rows,
            "good_originals": good_originals, "top_rank_plants": recovered_plants,
            "passed": good_originals >= 8 and recovered_plants >= 8}


if __name__ == "__main__":
    result = controls()
    (HERE / "controls.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: result[k] for k in ("good_originals", "top_rank_plants", "passed")}))
