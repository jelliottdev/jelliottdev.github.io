"""Run the frozen two-clock source branch and matched whole-search controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random

import numpy as np

from core import normalized_ioc_many, parse, source_score, unique_grid

HERE = pathlib.Path(__file__).resolve().parent


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def one_search(cipher: np.ndarray, prior: np.ndarray, bigrams: dict, trigrams: set) -> dict:
    outputs, settings = unique_grid(cipher, prior)
    measures = normalized_ioc_many(outputs)
    passing = np.flatnonzero(measures > 1.4)
    best = None
    for row in passing:
        score, bg, tg = source_score(outputs[row], float(measures[row]), bigrams, trigrams)
        if best is None or score > best["score"]:
            sign, letter, separator = (int(v) for v in settings[row])
            best = {
                "score": score,
                "ioc": float(measures[row]),
                "bigram_score": bg,
                "trigram_hits": tg,
                "effective": [sign, letter, separator],
                "decoded_sha256": sha(bytes(outputs[row])),
                "first_60": outputs[row, :60].tolist(),
            }
    return {
        "runes": int(len(cipher)),
        "unique_decodes": len(outputs),
        "named_source_settings": 5046,
        "passing_source_ioc_gate": int(len(passing)),
        "max_ioc": float(measures.max()),
        "best_gated": best,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    plan_blob = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_blob)
    inputs_blob = (HERE / "inputs.json").read_bytes()
    assert sha(inputs_blob) == plan["inputs_sha256"]
    data = json.loads(inputs_blob)
    gate = json.loads((HERE / "gate_results.json").read_text(encoding="utf-8"))
    assert gate["plan_sha256"] == sha(plan_blob) and gate["passed"]
    bigrams = {(a, b): v for a, b, v in data["bigrams"]}
    trigrams = {tuple(t) for t in data["trigrams"]}
    rows = []
    null_maxima = {"literal": [], "canonical": []}
    for parser, alphabet in (("literal", data["source_literal_runes"]), ("canonical", data["canonical_runes"])):
        targets = []
        for page in data["pages"]:
            cipher, prior = parse(page["text"], alphabet, data["separators"])
            obs = one_search(cipher, prior, bigrams, trigrams)
            rows.append({"parser": parser, "source_ordinal": page["source_ordinal"], "manuscript_page": page["manuscript_page"], **obs})
            if page["source_ordinal"] != 15:
                targets.append((page["source_ordinal"], cipher, prior))
        for trial in range(49):
            selected_score = None
            selected_page = None
            selected_gate_rows = 0
            for ordinal, cipher, prior in targets:
                trial_cipher = cipher.copy()
                rng = random.Random(330123 + 1000 * trial + ordinal)
                shuffled = trial_cipher.tolist()
                rng.shuffle(shuffled)
                trial_cipher = np.asarray(shuffled, dtype=np.int16)
                found = one_search(trial_cipher, prior, bigrams, trigrams)
                selected_gate_rows += found["passing_source_ioc_gate"]
                item = found["best_gated"]
                if item is not None and (selected_score is None or item["score"] > selected_score):
                    selected_score = item["score"]
                    selected_page = ordinal
            null_maxima[parser].append({"trial": trial, "best_score": selected_score, "source_ordinal": selected_page, "gated_unique_outputs": selected_gate_rows})
            if trial % 10 == 9:
                print(parser, "null", trial + 1, "/ 49", flush=True)
    result = {
        "schema": "wulfic-separator-clock-results-v1",
        "plan_sha256": sha(plan_blob),
        "inputs_sha256": sha(inputs_blob),
        "gate_sha256": sha((HERE / "gate_results.json").read_bytes()),
        "rows": rows,
        "null_maxima": null_maxima,
    }
    blob = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path = HERE / "results.json"
    if args.check:
        assert path.read_bytes() == blob
        print("deterministic results match", sha(blob))
    else:
        path.write_bytes(blob)
        print("saved", sha(blob))


if __name__ == "__main__":
    main()
