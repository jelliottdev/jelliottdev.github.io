"""Independent reconstruction of every observed and shuffled source gate."""
from __future__ import annotations

import hashlib
import json
import pathlib
import random

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent


def parse_independent(text: str, alphabet: str, separators: str):
    lookup = dict(zip(alphabet, range(29)))
    values, cuts = [], set()
    for glyph in text:
        if glyph in lookup:
            values.append(lookup[glyph])
        elif glyph in separators:
            cuts.add(len(values))
    prior = [sum(1 for cut in cuts if 0 < cut <= i) for i in range(len(values))]
    return np.asarray(values, dtype=np.int32), np.asarray(prior, dtype=np.int32)


def census(cipher: np.ndarray, prior: np.ndarray, bigrams: dict, trigrams: set):
    n = len(cipher)
    index = np.arange(n, dtype=np.int32)
    rows = []
    descriptors = []
    for sign in (1, -1):
        for letter in range(29):
            for separator in range(29):
                rows.append((sign * cipher + letter * index + separator * prior) % 29)
                descriptors.append((sign, letter, separator))
    matrix = np.asarray(rows, dtype=np.int32)
    freqs = np.zeros((len(matrix), 29), dtype=np.int32)
    for value in range(29):
        freqs[:, value] = (matrix == value).sum(axis=1)
    iocs = 29 * (freqs * (freqs - 1)).sum(axis=1) / (n * (n - 1))
    passing = np.flatnonzero(iocs > 1.4)
    top = None
    for idx in passing:
        seq = matrix[idx].tolist()
        bg = sum(bigrams.get((x, y), 0) for x, y in zip(seq, seq[1:]))
        tg = sum((x, y, z) in trigrams for x, y, z in zip(seq, seq[1:], seq[2:]))
        score = float(iocs[idx] + .01 * bg + .05 * tg)
        if top is None or score > top["score"]:
            top = {"score": score, "ioc": float(iocs[idx]), "bigram_score": bg, "trigram_hits": tg,
                   "effective": list(descriptors[idx]), "decoded_sha256": hashlib.sha256(bytes(seq)).hexdigest(),
                   "first_60": seq[:60]}
    return len(passing), float(iocs.max()), top


def main() -> None:
    plan_blob = (HERE / "plan.json").read_bytes()
    inputs_blob = (HERE / "inputs.json").read_bytes()
    plan = json.loads(plan_blob)
    assert hashlib.sha256(inputs_blob).hexdigest() == plan["inputs_sha256"]
    d = json.loads(inputs_blob)
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256(plan_blob).hexdigest()
    assert result["inputs_sha256"] == hashlib.sha256(inputs_blob).hexdigest()
    gate_blob = (HERE / "gate_results.json").read_bytes()
    assert result["gate_sha256"] == hashlib.sha256(gate_blob).hexdigest()
    assert json.loads(gate_blob)["passed"]
    bigrams = {(a, b): weight for a, b, weight in d["bigrams"]}
    trigrams = {tuple(v) for v in d["trigrams"]}
    checked = 0
    for parser, alphabet in (("literal", d["source_literal_runes"]), ("canonical", d["canonical_runes"])):
        target_pages = []
        for page in d["pages"]:
            c, prior = parse_independent(page["text"], alphabet, d["separators"])
            saved = next(r for r in result["rows"] if r["parser"] == parser and r["source_ordinal"] == page["source_ordinal"])
            passed, maximum, best = census(c, prior, bigrams, trigrams)
            assert len(c) == saved["runes"]
            assert passed == saved["passing_source_ioc_gate"]
            assert abs(maximum - saved["max_ioc"]) < 1e-12
            assert best == saved["best_gated"]
            checked += 1
            if page["source_ordinal"] != 15:
                target_pages.append((page["source_ordinal"], c, prior))
        for trial in range(49):
            best_score, best_page, gated_total = None, None, 0
            for ordinal, c, prior in target_pages:
                vals = c.tolist()
                random.Random(330123 + 1000 * trial + ordinal).shuffle(vals)
                passed, _, best = census(np.asarray(vals, dtype=np.int32), prior, bigrams, trigrams)
                gated_total += passed
                if best and (best_score is None or best["score"] > best_score):
                    best_score, best_page = best["score"], ordinal
            assert result["null_maxima"][parser][trial] == {"trial": trial, "best_score": best_score,
                                                                "source_ordinal": best_page,
                                                                "gated_unique_outputs": gated_total}
            checked += 1
    print("independently reconstructed", checked, "page or whole-search results")


if __name__ == "__main__":
    main()
