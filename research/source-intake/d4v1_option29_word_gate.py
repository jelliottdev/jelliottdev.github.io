"""Exploratory exact-preimage gate for the option-29 ciphertext-word rule.

This uses the documented warning's visible separators as idealized independent
word boundaries. It does not repair or replay the source's later delimiter clock.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "data/index.json": "c10e910560d8e82c8209fc01eaa477671df0b20875202f601893b9ce3c6f595a",
    "data/pages/lp1-01.json": "5c93bc312f1608038f486d86f6560cd5635e142e9a521a1df0984c21aca7a0d0",
    "exports/readings/warning.csv": "ca41950661c32c341c9d18a4330ea25129c609efa306377cc51fc5b1cea4a121",
}


def load(name):
    data = (ROOT / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == FILES[name], name
    return data


def phi(value):
    return sum(math.gcd(value, j) == 1 for j in range(1, value + 1))


def main():
    alphabet = json.loads(load("data/index.json"))["alphabet"]
    text = json.loads(load("data/pages/lp1-01.json"))["raw"]
    runes = {a["rune"] for a in alphabet}
    words = [len(word) for word in "".join(ch if ch in runes else " " for ch in text).split()]
    plain = [int(row["output_index"]) for row in csv.DictReader(load("exports/readings/warning.csv").decode("utf-8").splitlines())]
    assert len(words) == 50 and sum(words) == len(plain) == 184
    none = []
    pos = 0
    for n, length in enumerate(words):
        wanted = plain[pos:pos + length]
        candidates = []
        for shift in range(29):
            cipher = [(value + shift) % 29 for value in wanted]
            source_shift = phi(sum(alphabet[value]["prime"] for value in cipher)) % 29
            if source_shift == shift:
                candidates.append(shift)
        if not candidates:
            none.append(n)
        pos += length
    assert len(none) == 18 and none[0] == 0, none
    first = [(i, alphabet[i]["prime"], phi(alphabet[i]["prime"]) % 29,
              (i - phi(alphabet[i]["prime"])) % 29) for i in range(29)]
    assert all(output != plain[0] for _, _, _, output in first)
    print("18 of 50 warning words lack an idealized same-word preimage; first word A has none")


if __name__ == "__main__":
    main()
