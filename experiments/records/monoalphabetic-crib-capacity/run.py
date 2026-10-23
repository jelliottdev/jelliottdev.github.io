"""Count bijective GP29 substitution keys compatible with frozen page-start cribs."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
INPUTS = {item["path"]: item["sha256"] for item in PLAN["inputs"]}


def source(relative):
    data = (ROOT / relative).read_bytes()
    if hashlib.sha256(data).hexdigest() != INPUTS[relative]:
        raise ValueError(f"Changed input: {relative}")
    return data


def assess(cipher, proposed, continuation, modulus):
    """A partial bijection has (q-m)! extensions when both directions agree."""
    forward, backward = {}, {}
    for c, p in zip(cipher, proposed, strict=True):
        if c in forward and forward[c] != p or p in backward and backward[p] != c:
            return 0, 0, None
        forward[c], backward[p] = p, c
    m = len(forward)
    forced = sum(c in forward for c in continuation)
    return m, math.factorial(modulus - m), forced


def controls():
    count = 0
    for q, length, patterns in (
        (3, 4, ((0, 0, 1, 2), (0, 1, 0, 1), (0, 1, 2, 0))),
        (5, 4, ((0, 1, 2, 3), (0, 0, 1, 2), (0, 1, 0, 1))),
    ):
        keys = tuple(itertools.permutations(range(q)))
        for cipher in patterns:
            for proposed in itertools.product(range(q), repeat=length):
                _, expected, _ = assess(cipher, proposed, (), q)
                exhaustive = sum(all(key[c] == p for c, p in zip(cipher, proposed)) for key in keys)
                assert expected == exhaustive
                count += 1
    trace = source("exports/readings/warning.csv").decode("utf-8-sig")
    plain = [int(row["output_index"]) for row in csv.DictReader(trace.splitlines())][:24]
    assert len(plain) == 24
    # Invert a fixed affine permutation to manufacture a known complete reading.
    a, b = 7, 11
    cipher = [(pow(a, -1, 29) * (p - b)) % 29 for p in plain]
    m, keys, forced = assess(cipher[:12], plain[:12], cipher[12:], 29)
    assert keys == math.factorial(29 - m)
    assert all((a * c + b) % 29 == p for c, p in zip(cipher, plain))
    assert forced == sum(c in cipher[:12] for c in cipher[12:])
    return {"toy_exhaustive_comparisons": count, "planted": {"reading": "warning", "runes": 24, "assigned_symbols": m, "compatible_keys": str(keys), "following_positions_forced": forced}, "passed": True}


def produce():
    control = controls()
    alphabet = json.loads(source("data/index.json"))["alphabet"]
    lookup = {item["rune"]: i for i, item in enumerate(alphabet)}
    known = json.loads(source("experiments/records/lp2-known-vigenere-keys/plan.json"))
    openings = [(item["id"], item["indices"]) for item in known["openings"]]
    assert len(openings) == 9 and all(len(indices) == 12 for _, indices in openings)
    rows = []
    for page_id in PLAN["pages"]:
        page = json.loads(source(f"data/pages/{page_id}.json"))
        stream = [lookup[r] for line in page["lines"] for r in line["raw"] if r in lookup]
        assert len(stream) == page["rune_count"] and len(stream) >= 24
        for crib_id, proposed in openings:
            assigned, keys, forced = assess(stream[:12], proposed, stream[12:24], 29)
            rows.append({"page": page_id, "crib": crib_id, "compatible": keys > 0,
                         "assigned_symbols": assigned, "compatible_keys": str(keys),
                         "following_positions_forced": forced})
    assert len(rows) == 55 * 9
    empty = json.loads(source("data/pages/lp2-50.json"))
    assert empty["rune_count"] == 0
    fitting = [row for row in rows if row["compatible"]]
    return {"schema": "liberpedia-monoalphabetic-crib-capacity-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "control": control, "page_count": 55, "crib_count": 9, "case_count": len(rows),
            "compatible_count": len(fitting), "impossible_count": len(rows) - len(fitting),
            "assigned_symbol_range": [min((row["assigned_symbols"] for row in fitting), default=None), max((row["assigned_symbols"] for row in fitting), default=None)],
            "forced_next12_range": [min((row["following_positions_forced"] for row in fitting), default=None), max((row["following_positions_forced"] for row in fitting), default=None)],
            "cases": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = produce()
    path = HERE / "results.json"
    if args.check:
        assert result == json.loads(path.read_text(encoding="utf-8"))
        print("PASS: complete monoalphabetic crib census and planted controls")
    else:
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print({key: result[key] for key in ("case_count", "compatible_count", "assigned_symbol_range", "forced_next12_range")})
