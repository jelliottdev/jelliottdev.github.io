"""Rebuild every square-derived title decode from site runes and arithmetic."""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAMES = ("cell values", "primes p(F+1)", "phi = p(F+1) - 1", "ordinals F+1", "Fibonacci F")
MODES = ("sub", "add", "beaufort")


def primes_through(k: int) -> list[int]:
    result = []
    candidate = 2
    while len(result) <= k:
        if all(candidate % p for p in result if p * p <= candidate):
            result.append(candidate)
        candidate += 1
    return result


def source_keys() -> dict[str, list[int]]:
    fib = []
    a, b = 0, 1
    while len(fib) < 16:
        if a not in fib:
            fib.append(a)
        a, b = b, a + b
    primes = primes_through(fib[-1])
    values = [primes[f] for f in fib]
    return {"cell values": [abs(3301 - v) for v in values],
            "primes p(F+1)": values,
            "phi = p(F+1) - 1": [v - 1 for v in values],
            "ordinals F+1": [f + 1 for f in fib],
            "Fibonacci F": fib}


def verify() -> dict:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    rune_to_index = {e["rune"]: e["index"] for e in index}
    latin = {e["index"]: e["latin"] for e in index}
    raw = json.loads((ROOT / "data/pages/lp2-15.json").read_text(encoding="utf-8"))["raw"]
    header = raw.split("/", 1)[0]
    words = [[rune_to_index[c] for c in word if c in rune_to_index] for word in header.split("-")]
    assert list(map(len, words)) == [4, 5]
    assert words == [[0, 1, 20, 19], [24, 28, 26, 22, 24]]
    keys = source_keys()
    assert tuple(keys) == NAMES
    printed = [int(v) for v in re.findall(r"\b\d+\b", raw.split("$", 1)[0])]
    assert len(printed) == 16 and sorted(printed) == sorted(keys["cell values"])

    source = (HERE / "source-title-output.txt").read_text(encoding="utf-8").splitlines()
    assert "0/20000" in source[1]
    decoded = []
    for line in source:
        match = re.search(r"\b(outward|inward)\s+(sub|add|beaufort)\s+(\S+)\s+(\S+)$", line)
        if not match:
            continue
        direction, mode, first, second = match.groups()
        name = line[:match.start()].strip().removeprefix("fail").removeprefix("PASS").strip()
        assert name in keys, (name, line)
        values = keys[name] if direction == "outward" else list(reversed(keys[name]))
        ciphertext = words[0] + words[1]
        if mode == "sub":
            plain = [(c - k) % 29 for c, k in zip(ciphertext, values)]
        elif mode == "add":
            plain = [(c + k) % 29 for c, k in zip(ciphertext, values)]
        else:
            plain = [(k - c) % 29 for c, k in zip(ciphertext, values)]
        expected = ("-".join(latin[v] for v in plain[:4]), "-".join(latin[v] for v in plain[4:]))
        assert (first, second) == expected, (name, direction, mode, expected, (first, second))
        decoded.append((name, direction, mode, first, second))
        assert line.strip().startswith("fail")
    assert len(decoded) == len(set((n, d, m) for n, d, m, _, _ in decoded)) == 30
    assert source[-1].startswith("Title verdict: 0/30 decodes pass")
    return {"source_cases": 30, "source_passes": 0, "source_random_key_hits": 0,
            "source_random_key_draws": 20000, "title_runes": 9,
            "square_entries": len(printed), "key_sources": len(keys), "directions": 2, "operations": 3,
            "decodes": [{"source": n, "direction": d, "operation": m,
                         "first_word": f, "second_word": s} for n, d, m, f, s in decoded]}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
