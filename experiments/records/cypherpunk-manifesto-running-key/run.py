"""Whole-page additive running-key search against a pinned manifesto text."""

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import random
import re
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_letters(raw):
    document = raw.decode("latin-1")
    start = document.index("Privacy is necessary")
    finish = document.index("Eric Hughes", document.index("Onward.", start))
    body = re.sub(r"<[^>]*>", " ", document[start:finish])
    return "".join(c for c in html.unescape(body).upper() if "A" <= c <= "Z")


def key_variants(source, alphabet):
    ordinary = [ord(c) - ord("A") for c in source]
    labels = sorted(((row["latin"], i) for i, row in enumerate(alphabet)),
                    key=lambda pair: -len(pair[0]))
    aliases = {"V": 1, "K": 5, "Z": 15, "Q": 5}
    gp = []
    position = 0
    while position < len(source):
        for label, index in labels:
            if source.startswith(label, position):
                gp.append(index)
                position += len(label)
                break
        else:
            gp.append(aliases[source[position]])
            position += 1
    return {"ascii-ordinal": ordinary, "gp-greedy": gp}


def quadgram_model():
    table = {}
    model_path = ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt"
    for line in model_path.read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        table[gram] = int(count)
    total = sum(table.values())
    divisor = math.log10(total)
    return ({gram: math.log10(count) - divisor for gram, count in table.items()},
            math.log10(0.01) - divisor, len(table), total)


def score(text, log_probability, floor):
    count = len(text) - 3
    return sum(log_probability.get(text[i:i + 4], floor) for i in range(count)) / count


def search(cipher, key, labels, log_probability, floor, top_n=5):
    offsets = len(key) - len(cipher) + 1
    assert offsets > 0
    best = []
    for offset in range(offsets):
        output = "".join(labels[(c - key[offset + i]) % 29] for i, c in enumerate(cipher))
        value = score(output, log_probability, floor)
        candidate = (value, -offset, output)
        if len(best) < top_n or candidate[:2] > best[-1][:2]:
            best.append(candidate)
            best.sort(key=lambda row: row[:2], reverse=True)
            del best[top_n:]
    return {
        "offsets_searched": offsets,
        "top": [
            {"offset_zero_based": -neg_offset, "score": value,
             "latin": output, "latin_sha256": digest(output.encode("ascii"))}
            for value, neg_offset, output in best
        ],
    }


def load_inputs():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    for row in plan["inputs"]:
        assert digest((ROOT / row["path"]).read_bytes()) == row["sha256"], row["path"]
    source = source_letters((HERE / "source.html").read_bytes())
    assert len(source) == plan["source_normalized_letters"]
    assert digest(source.encode("ascii")) == plan["source_normalized_sha256"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    labels = [row["latin"] for row in alphabet]
    keys = key_variants(source, alphabet)
    for row in plan["key_variants"]:
        key = keys[row["id"]]
        assert len(key) == row["key_length"]
        if "key_sha256" in row:
            assert digest(bytes(key)) == row["key_sha256"]
    index = {row["rune"]: i for i, row in enumerate(alphabet)}
    page_indices = {}
    for page in plan["targets"]:
        raw = (ROOT / "text" / f"{page}.txt").read_text(encoding="utf-8")
        page_indices[page] = [index[c] for c in raw if c in index]
    log_probability, floor, gram_count, total = quadgram_model()
    return plan_bytes, plan, keys, labels, page_indices, log_probability, floor, gram_count, total


def positive_controls(keys, labels, logp, floor):
    known = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    welcome = next(row for row in known["controls"] if row["id"] == "welcome")
    plain = next(row for row in welcome["decoded_pages"] if row["page"] == "lp1-04")["rune_indices"]
    assert len(plain) == 264
    planted_offset = 3301
    controls = []
    for variant, key in keys.items():
        synthetic = [(p + key[planted_offset + i]) % 29 for i, p in enumerate(plain)]
        plant = search(synthetic, key, labels, logp, floor)
        assert [(c - key[planted_offset + i]) % 29 for i, c in enumerate(synthetic)] == plain
        selected = plant["top"][0]["offset_zero_based"] == planted_offset
        controls.append({
            "variant": variant, "page": "lp1-04", "runes": len(plain),
            "offset_zero_based": planted_offset, "true_offset_selected_first": selected,
            "known_plaintext_score": score("".join(labels[p] for p in plain), logp, floor),
            "search": plant,
        })
    return controls


def report():
    plan_bytes, plan, keys, labels, pages, logp, floor, gram_count, total = load_inputs()
    positive = positive_controls(keys, labels, logp, floor)
    assert all(row["true_offset_selected_first"] for row in positive), "positive-control gate failed"
    targets = []
    seeds = range(330100, 330116)
    for variant, key in keys.items():
        shuffled_keys = []
        for seed in seeds:
            shuffled = key.copy()
            random.Random(seed).shuffle(shuffled)
            shuffled_keys.append((seed, shuffled, digest(bytes(shuffled))))
        for page, cipher in pages.items():
            original = search(cipher, key, labels, logp, floor)
            controls = []
            for seed, shuffled, key_sha in shuffled_keys:
                control = search(cipher, shuffled, labels, logp, floor, top_n=1)
                controls.append({"seed": seed, "key_sha256": key_sha,
                                 "maximum": control["top"][0]["score"],
                                 "offset_zero_based": control["top"][0]["offset_zero_based"]})
            original_best = original["top"][0]["score"]
            targets.append({
                "variant": variant, "page": page, "page_runes": len(cipher),
                "offsets_searched": original["offsets_searched"],
                "original_top_five": original["top"], "shuffle_maxima": controls,
                "shuffles_at_least_as_high": sum(c["maximum"] >= original_best for c in controls),
            })
    return {
        "schema": "liberpedia-manifesto-running-key-results-v1",
        "plan_sha256": digest(plan_bytes),
        "source_keys": [{"variant": variant, "length": len(key), "sha256": digest(bytes(key))}
                        for variant, key in keys.items()],
        "quadgram_count": gram_count, "quadgram_total": total,
        "score_floor": floor, "positive_control": positive, "targets": targets,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true", help="Time one source search, with no result write")
    parser.add_argument("--controls", action="store_true", help="Run only the planted positive-control gate")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.benchmark:
        _, _, keys, labels, pages, logp, floor, _, _ = load_inputs()
        start = time.perf_counter()
        row = search(pages["lp2-00"], keys["ascii-ordinal"], labels, logp, floor)
        print(json.dumps({"seconds": round(time.perf_counter() - start, 3),
                          "offsets": row["offsets_searched"]}))
        return
    if args.controls:
        _, _, keys, labels, _, logp, floor, _, _ = load_inputs()
        controls = positive_controls(keys, labels, logp, floor)
        assert all(row["true_offset_selected_first"] for row in controls), "positive-control gate failed"
        print(json.dumps({"positive_gate": [(row["variant"], row["true_offset_selected_first"])
                                             for row in controls]}))
        return
    output = report()
    path = HERE / "results.json"
    if args.check:
        assert output == json.loads(path.read_text(encoding="utf-8"))
        print("PASS: complete manifesto running-key searches reproduce")
    else:
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"positive_selected": [(row["variant"], row["true_offset_selected_first"])
                                                for row in output["positive_control"]],
                          "targets": [(row["variant"], row["page"], row["shuffles_at_least_as_high"])
                                      for row in output["targets"]]}))


if __name__ == "__main__":
    main()
