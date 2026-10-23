"""Post-target audit of the original author's complete-page positional hit rule."""
import csv
import hashlib
import json
from pathlib import Path
import random

import numpy as np
from numba import njit

import run

HERE = Path(__file__).resolve().parent
RECEIPT = json.loads((HERE / "source-control.json").read_text(encoding="utf-8"))
TARGET = np.array(RECEIPT["source_unigram_target"], dtype=np.float64)


@njit
def source_scores(cipher, keys, target):
    output = np.empty(len(keys), dtype=np.float64)
    for offset in range(len(keys)):
        counts = np.zeros(29, dtype=np.float64)
        for i in range(len(cipher)):
            counts[(cipher[i] - keys[offset, i] + 29) % 29] += 1
        divergence = 0.0
        for rune in range(29):
            observed = counts[rune] / len(cipher)
            expected = target[rune]
            middle = (observed + expected) / 2
            if observed:
                divergence += 0.5 * observed * np.log(observed / middle)
            if expected:
                divergence += 0.5 * expected * np.log(expected / middle)
        output[offset] = 1 / (1 + divergence)
    return output


def hits(cipher, keys):
    values = source_scores(cipher, keys, TARGET)
    mean = float(np.mean(values))
    std = float(np.sqrt(np.mean(values * values) - mean * mean))
    z = (values - mean) / (std + 0.00001)
    choices = [(int(i), float(values[i]), float(z[i])) for i in range(len(keys))
               if values[i] > 0.90 and z[i] > 3.5]
    return choices, values


def produce():
    lookup, *_ = run.setup()
    streams, _, _ = run.page_data(lookup)
    max_len = max(1000, max(map(len, streams)))
    keys = np.array([[run.phi(i + offset) % 29 for i in range(max_len)]
                     for offset in range(100)], dtype=np.int64)
    # Source exact operator; cloned source uses native whole-page rune order.
    actual = []
    for page, stream in zip(run.PLAN["pages"], streams):
        found, _ = hits(np.array(stream, dtype=np.int64), keys)
        actual.extend({"page": page, "offset": off, "fitness": fit, "z": z} for off, fit, z in found)
    plants = []
    for name in run.PLAN["readings"]:
        body = run.read_pinned(f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = np.array([int(row["output_index"]) for row in csv.DictReader(body.splitlines())], dtype=np.int64)
        cipher = (plain + keys[17, :len(plain)]) % 29
        found, values = hits(cipher, keys)
        plants.append({"reading": name, "true_offset_hit": any(off == 17 for off, _, _ in found),
                       "true_offset_fitness": float(values[17]), "hit_offsets": [off for off, _, _ in found]})
    null_counts = []
    for rep in range(199):
        count = 0
        for index, stream in enumerate(streams):
            copy = list(stream)
            random.Random(3301 + 10000 * rep + index).shuffle(copy)
            found, _ = hits(np.array(copy, dtype=np.int64), keys)
            count += len(found)
        null_counts.append(count)
    return {"schema": "liberpedia-d4v1-source-positional-audit-v1",
            "timing": "Post-target source-rule audit; not part of the frozen English-score plan",
            "source_revision": RECEIPT["source_revision"],
            "source_rule": "All 100 offsets for each complete page; hit iff fitness>0.90 and (fitness-mean)/(population_std+0.00001)>3.5",
            "actual_hits": actual, "planted_controls": plants,
            "null_hit_counts": null_counts,
            "null_replicates_with_a_hit": sum(x > 0 for x in null_counts),
            "scope": "Whole-page positional hit rule only; 199 full 55-page × 100-offset shuffled selection controls. Its low-power source gate is reported, not used to certify a ciphertext exclusion."}


if __name__ == "__main__":
    path = HERE / "source-positional.json"
    result = produce()
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert saved == result
        print("Source positional gate audit matches saved receipt")
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print("Saved post-target source positional audit")
