"""Independent packet parser, page reconstruction and complete-search verifier."""
import base64
import csv
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np

from engine import search, BASE

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
pins = {row["path"]: row["sha256"] for row in plan["inputs"]}
assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == saved["plan_sha256"]


def pinned(relative):
    data = (ROOT / relative).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[relative]
    return data


def packet_bodies(armored):
    # Parse the actual armor and packet lengths without calling the producer's
    # material extractor. This file has only definite-length packet headers.
    payload_lines = armored.split(b"-----BEGIN PGP PUBLIC KEY BLOCK-----", 1)[1].split(b"-----END PGP PUBLIC KEY BLOCK-----", 1)[0].splitlines()
    encoded = b"".join(line.strip() for line in payload_lines if line.strip() and not line.startswith(b"=") and b":" not in line)
    payload = base64.b64decode(encoded, validate=True)
    found = []
    at = 0
    while at < len(payload):
        header = payload[at]
        assert header >= 128
        at += 1
        if header & 64:
            tag = header & 63
            first = payload[at]
            at += 1
            if first < 192:
                size = first
            elif first < 224:
                size = 192 + ((first - 192) << 8) + payload[at]
                at += 1
            else:
                assert first == 255
                size = int.from_bytes(payload[at:at + 4], "big")
                at += 4
        else:
            tag = (header >> 2) & 15
            form = header & 3
            assert form != 3
            width = (1, 2, 4)[form]
            size = int.from_bytes(payload[at:at + width], "big")
            at += width
        body = payload[at:at + size]
        assert len(body) == size
        at += size
        if tag in (6, 14):
            assert body[0] == 4 and body[5] in (1, 2, 3)
            fingerprint = hashlib.sha1(bytes((153,)) + len(body).to_bytes(2, "big") + body).digest()
            found.append(("primary" if tag == 6 else "subkey", body, fingerprint))
    assert [row[0] for row in found] == ["primary", "subkey"]
    return found


armor_path = "experiments/records/public-rsa-payload-e01/source/corpus/A-primary-artifacts/pgp/keys/cicada-3301-pubkey.keys.openpgp.org.asc"
packets = packet_bodies(pinned(armor_path))
materials = [("primary-packet", packets[0][1]), ("primary-fingerprint", packets[0][2]),
             ("subkey-packet", packets[1][1]), ("subkey-fingerprint", packets[1][2])]
assert [row[0] for row in materials] == plan["key_order"]
for role, _, fingerprint in packets:
    assert fingerprint.hex() == plan["expected_fingerprints"][role]
assert [{"name": name, "length": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in materials] == saved["source"]
periods = np.array([len(data) for _, data in materials], dtype=np.int64)
starts = np.array([sum(periods[:i]) for i in range(4)], dtype=np.int64)
keys = np.array([byte % 29 for _, data in materials for byte in data], dtype=np.int64)

alphabet = json.loads(pinned("data/index.json"))["alphabet"]
lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
labels = [row["latin"] for row in alphabet]
symbols = np.zeros((29, 2), dtype=np.int64)
sizes = np.zeros(29, dtype=np.int64)
for i, label in enumerate(labels):
    sizes[i] = len(label)
    for j, letter in enumerate(label):
        symbols[i, j] = ord(letter) - 65
count_table = {gram: int(amount) for gram, amount in (line.split() for line in pinned(plan["score_model"]).decode("ascii").splitlines())}
norm = math.log10(sum(count_table.values()))
floor = math.log10(0.01) - norm
weights = np.full(BASE, floor, dtype=np.float64)
for gram, amount in count_table.items():
    index = 0
    for letter in gram:
        index = index * 26 + ord(letter) - 65
    weights[index] = math.log10(amount) - norm


def string_score(indices):
    text = "".join(labels[int(i)] for i in indices)
    return sum(math.log10(count_table.get(text[i:i + 4], 0.01)) - norm
               for i in range(len(text) - 3)) / (len(text) - 3)


known_scores = []
for name in plan["controls"]["readings"]:
    trace = pinned(f"exports/readings/{name}.csv").decode("utf-8-sig")
    known_scores.append(string_score([int(row["output_index"]) for row in csv.DictReader(trace.splitlines())][:66]))
assert all(row["exact_recovery"] for row in saved["control_gate"]["rows"])
for row, direct in zip(saved["control_gate"]["rows"], known_scores):
    assert abs(row["score"] - direct) < 1e-11
assert saved["control_gate"]["passed"] and saved["control_gate"]["readings_above_threshold"] == 9

sequences = []
for name in plan["pages"]:
    doc = json.loads(pinned(f"data/pages/{name}.json"))
    values = [lookup[rune] for rune in doc["raw"] if rune in lookup]
    assert len(values) == doc["rune_count"] and len(values) >= 66
    sequences.append(values)
assert json.loads(pinned("data/pages/lp2-50.json"))["rune_count"] == 0
lengths = np.array([len(row) for row in sequences], dtype=np.int64)
pages = np.zeros((55, int(lengths.max())), dtype=np.int64)
for i, row in enumerate(sequences):
    pages[i, :len(row)] = row

observed = search(pages, lengths, keys, starts, periods, symbols, sizes, weights)
assert observed.shape == (55, 2180) and observed.size == saved["case_count"] == 119900
assert hashlib.sha256(observed.astype("<f8").tobytes()).hexdigest() == saved["score_matrix_sha256"]
assert np.count_nonzero(observed >= plan["score_threshold"]) == saved["threshold_passes"]


def column(group, phase, sign):
    return 2 * sum(periods[:group]) + 2 * phase + (0 if sign == -1 else 1)


for row in saved["stream_maxima"]:
    group = plan["key_order"].index(row["material"])
    p = plan["pages"].index(row["page"])
    c = column(group, row["phase"], row["sign"])
    start, end = 2 * sum(periods[:group]), 2 * sum(periods[:group + 1])
    assert abs(observed[p, c] - row["score"]) < 1e-11
    assert abs(observed[:, start:end].max() - row["score"]) < 1e-11
    key = keys[starts[group]:starts[group] + periods[group]]
    decoded = [(int(value) + row["sign"] * int(key[(i + row["phase"]) % len(key)])) % 29
               for i, value in enumerate(sequences[p])]
    assert abs(string_score(decoded) - row["score"]) < 1e-11
for i, row in enumerate(saved["page_maxima"]):
    assert row["page"] == plan["pages"][i] and abs(row["score"] - observed[i].max()) < 1e-11
assert abs(saved["winner"]["score"] - observed.max()) < 1e-11

null_maxima = []
for rep in range(plan["null"]["replicates"]):
    surrogate = pages.copy()
    for p in range(55):
        row = surrogate[p, :lengths[p]].tolist()
        random.Random(plan["null"]["seed"] + 1000 * rep + p).shuffle(row)
        surrogate[p, :lengths[p]] = row
    null_maxima.append(float(search(surrogate, lengths, keys, starts, periods, symbols, sizes, weights).max()))
assert null_maxima == saved["null_global_maxima"]
tail = sum(score >= saved["winner"]["score"] for score in null_maxima)
assert tail == saved["null_at_least_best"]
assert (1 + tail) / (len(null_maxima) + 1) == saved["empirical_global_tail"]
print("PASS: independent OpenPGP parser, 119,900 scores, 199 full-search nulls and direct-string score checks")
