"""Independent scalar receipt checks, including one complete selected null search."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from engine import GOOD_MASK, MODES, lfsr_grid

HERE = Path(__file__).resolve().parent
GOOD = {(16, 8), (8, 18), (10, 9), (18, 4), (24, 9),
        (9, 23), (16, 10), (22, 0), (10, 16), (10, 15)}


def scalar_key(parameters: list[int], length: int) -> list[int]:
    a, b, x, y = parameters
    result = [a, b]
    while len(result) < length:
        result.append((x * result[-2] + y * result[-1]) % 29)
    return result[:length]


def scalar_score(values: list[int], key: list[int], positions: list[int], mode: str) -> tuple[dict, list[int]]:
    if mode == "sub":
        plain = [(c - k) % 29 for c, k in zip(values, key)]
    elif mode == "add":
        plain = [(c + k) % 29 for c, k in zip(values, key)]
    else:
        plain = [(k - c) % 29 for c, k in zip(values, key)]
    n = len(plain)
    counts = Counter(plain)
    ioc = 29 * sum(q * (q - 1) for q in counts.values()) / (n * (n - 1))
    bg = sum(pair in GOOD for pair in zip(plain[:-1], plain[1:]))
    sh = sum(plain[p] in (10, 24) for p in positions)
    return ({"ioc": ioc, "bigrams": bg, "single_hits": sh, "single_total": len(positions),
             "combined": ioc + 0.1 * bg + 5 * sh / max(1, len(positions))}, plain)


def single_positions(lengths: list[int]) -> list[int]:
    pos = 0; result = []
    for width in lengths:
        if width == 1:
            result.append(pos)
        pos += width
    return result


def verify() -> None:
    plan_raw = (HERE / "plan.json").read_bytes()
    inputs_raw = (HERE / "inputs.json").read_bytes()
    gate_raw = (HERE / "gate.json").read_bytes()
    results = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    inputs = json.loads(inputs_raw)
    assert results["plan_sha256"] == hashlib.sha256(plan_raw).hexdigest()
    assert results["inputs_sha256"] == hashlib.sha256(inputs_raw).hexdigest()
    assert results["gate_sha256"] == hashlib.sha256(gate_raw).hexdigest()
    assert len(inputs["pages"]) == 38
    assert results["target_pages"] == [p["page"] for p in inputs["pages"]]
    pages = {p["page"]: p for p in inputs["pages"]}
    selected = sorted(inputs["pages"], key=lambda p: -len(single_positions(p["word_lengths"])))[:3]
    assert [p["page"] for p in selected] == results["lfsr_selected_pages"]
    assert results["observed"]["streams"]["settings"] == 38 * 26 * 3
    assert results["observed"]["lfsr"]["settings"] == 3 * 29 ** 4 * 3
    # Every retained LFSR winner is recomputed with a separate recurrence and score.
    for row in results["observed"]["lfsr"]["pages"]:
        page = pages[row["page"]]
        positions = single_positions(page["word_lengths"])
        assert row["singleton_count"] == len(positions)
        assert row["runes"] == len(page["values"])
        for candidate in row["top_10"]:
            key = scalar_key(candidate["state"] + candidate["taps"], len(page["values"]))
            metrics, plain = scalar_score(page["values"], key, positions, candidate["mode"])
            for field, value in metrics.items():
                if isinstance(value, float):
                    assert abs(candidate[field] - value) < 1e-12
                else:
                    assert candidate[field] == value
            assert candidate["decode_sha256"] == hashlib.sha256(bytes(plain)).hexdigest()
    # Independent closed-form prime sieve/streams can be compared with the 38 saved maxima.
    sieve = [True] * 100001
    sieve[0] = sieve[1] = False
    for i in range(2, 317):
        if sieve[i]:
            for j in range(i*i, 100001, i):
                sieve[j] = False
    primes = [i for i, valid in enumerate(sieve) if valid]
    def source_stream(name: str, length: int) -> list[int]:
        if name.startswith("totient_s"):
            s = int(name.split("s")[-1]); return [(primes[s+i] - 1) % 29 for i in range(length)]
        if name.startswith("prime_mod_s"):
            s = int(name.split("s")[-1]); return [primes[s+i] % 29 for i in range(length)]
        if name.startswith("cumul_totient_s"):
            s = int(name.split("s")[-1]); out=[]; value=0
            for i in range(length):
                value = (value + primes[s+i] - 1) % 29; out.append(value)
            return out
        if name.startswith("prime_gap_s"):
            s = int(name.split("s")[-1]); return [(primes[s+i+1] - primes[s+i]) % 29 for i in range(length)]
        shift = int(name[len("prime_minus"):-len("_s0")])
        return [(primes[i] - shift) % 29 for i in range(length)]
    for row in results["observed"]["streams"]["pages"]:
        page = pages[row["page"]]
        winner = row["best"]
        key = source_stream(winner["stream"], len(page["values"]))
        metrics, plain = scalar_score(page["values"], key, single_positions(page["word_lengths"]), winner["mode"])
        for field, value in metrics.items():
            assert abs(winner[field] - value) < 1e-12
        assert winner["decode_sha256"] == hashlib.sha256(bytes(plain)).hexdigest()
    control_rows = results["controls"]["rows"]
    assert len(control_rows) == results["controls"]["replicates"] == 19
    for metric, observed in (("stream_max_combined", results["observed"]["streams"]["max_combined"]),
                             ("stream_max_ioc", results["observed"]["streams"]["max_ioc"]),
                             ("lfsr_max_combined", results["observed"]["lfsr"]["max_combined"])):
        assert results["controls"][metric+"_exceedances"] == sum(row[metric] >= observed for row in control_rows)
    # Replay one full shuffled LFSR grid; per-candidate source parity is checked in gate.py.
    rng = np.random.default_rng(results["controls"]["seed"])
    shuffled = {p["page"]: rng.permutation(np.asarray(p["values"], dtype=np.int16)) for p in inputs["pages"]}
    total_hits = 0; peak = -1.0
    for page in selected:
        flags = np.zeros(len(page["values"]), dtype=np.uint8)
        flags[single_positions(page["word_lengths"])] = 1
        scores, hits = lfsr_grid(shuffled[page["page"]], flags, GOOD_MASK)
        total_hits += int(hits.sum())
        peak = max(peak, float(scores.max()))
    assert total_hits == control_rows[0]["lfsr_source_hits"]
    assert peak == control_rows[0]["lfsr_max_combined"]
    print("Independent scalar winner/digest checks, bounds, source inputs, and full null-0 LFSR replay passed.")


if __name__ == "__main__":
    verify()
