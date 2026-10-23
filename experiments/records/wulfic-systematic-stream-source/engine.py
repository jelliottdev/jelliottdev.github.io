"""Exact finite operators from pinned stream_cipher_attack.py; no language claim."""
from __future__ import annotations

from collections import Counter

import numpy as np
from numba import njit, prange

N = 29
MODES = ("sub", "add", "beaufort")
GOOD = ((16, 8), (8, 18), (10, 9), (18, 4), (24, 9),
        (9, 23), (16, 10), (22, 0), (10, 16), (10, 15))
GOOD_MASK = np.zeros((N, N), dtype=np.uint8)
for _a, _b in GOOD:
    GOOD_MASK[_a, _b] = 1
GRID_SIZE = N ** 4


def primes_through(limit: int = 100000) -> list[int]:
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    return [i for i, yes in enumerate(sieve) if yes]


PRIMES = primes_through()


def stream_names() -> list[str]:
    names: list[str] = []
    for i in range(10):
        names.extend((f"totient_s{i}", f"prime_mod_s{i}"))
    names += ["cumul_totient_s0", "cumul_totient_s1", "prime_gap_s0", "prime_gap_s1",
              "prime_minus2_s0", "prime_minus3_s0"]
    return names


def stream(name: str, length: int) -> np.ndarray:
    if name.startswith("totient_s"):
        start = int(name.split("s")[-1])
        values = [(PRIMES[start + i] - 1) % N for i in range(length)]
    elif name.startswith("prime_mod_s"):
        start = int(name.split("s")[-1])
        values = [PRIMES[start + i] % N for i in range(length)]
    elif name.startswith("cumul_totient_s"):
        start = int(name.split("s")[-1])
        s = 0; values = []
        for i in range(length):
            s = (s + PRIMES[start + i] - 1) % N
            values.append(s)
    elif name.startswith("prime_gap_s"):
        start = int(name.split("s")[-1])
        values = [(PRIMES[start + i + 1] - PRIMES[start + i]) % N for i in range(length)]
    elif name.startswith("prime_minus") and name.endswith("_s0"):
        sub = int(name[len("prime_minus"):-len("_s0")])
        values = [(PRIMES[i] - sub) % N for i in range(length)]
    else:
        raise ValueError(name)
    return np.asarray(values, dtype=np.int16)


def singleton_positions(lengths: list[int]) -> np.ndarray:
    pos = 0; singles = []
    for length in lengths:
        if length == 1:
            singles.append(pos)
        pos += length
    return np.asarray(singles, dtype=np.int32)


def decode(values: np.ndarray, key: np.ndarray, mode: str) -> np.ndarray:
    if mode == "sub":
        return (values - key) % N
    if mode == "add":
        return (values + key) % N
    if mode == "beaufort":
        return (key - values) % N
    raise ValueError(mode)


def score(values: np.ndarray, key: np.ndarray, singles: np.ndarray, mode: str) -> dict:
    plain = decode(values, key, mode)
    n = len(plain)
    freq = Counter(map(int, plain))
    ioc = N * sum(x * (x - 1) for x in freq.values()) / (n * (n - 1))
    bigrams = sum((int(a), int(b)) in GOOD for a, b in zip(plain[:-1], plain[1:]))
    single_hits = sum(int(plain[p]) in (10, 24) for p in singles)
    combined = ioc + bigrams * 0.1 + single_hits / max(len(singles), 1) * 5
    return {"ioc": ioc, "bigrams": bigrams, "single_hits": single_hits,
            "single_total": len(singles), "combined": combined}


def tuple_from_index(index: int) -> tuple[int, int, int, int]:
    c1 = index % N; index //= N
    c0 = index % N; index //= N
    s1 = index % N; index //= N
    return index, s1, c0, c1


def lfsr_key(state_taps: tuple[int, int, int, int], length: int) -> np.ndarray:
    s0, s1, c0, c1 = state_taps
    state = [s0, s1]
    for _ in range(length - 2):
        state.append((c0 * state[-2] + c1 * state[-1]) % N)
    return np.asarray(state[:length], dtype=np.int16)


@njit(parallel=True)
def lfsr_grid(values: np.ndarray, single_flags: np.ndarray, good: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return exact source combined scores and hit flags for all 29^4×3 settings."""
    count = N ** 4
    scores = np.empty((count, 3), dtype=np.float64)
    hits = np.empty((count, 3), dtype=np.uint8)
    n = len(values)
    singleton_total = 0
    for p in range(n):
        singleton_total += single_flags[p]
    den = n * (n - 1)
    for idx in prange(count):
        c1 = idx % N
        c0 = (idx // N) % N
        s1 = (idx // (N * N)) % N
        s0 = idx // (N * N * N)
        prev0 = s0; prev1 = s1
        freq = np.zeros((3, N), dtype=np.int32)
        prev_plain = np.zeros(3, dtype=np.int16)
        bg = np.zeros(3, dtype=np.int32)
        sh = np.zeros(3, dtype=np.int32)
        for p in range(n):
            if p == 0:
                key = s0
            elif p == 1:
                key = s1
            else:
                key = (c0 * prev0 + c1 * prev1) % N
                prev0 = prev1; prev1 = key
            c = values[p]
            d0 = (c - key) % N
            d1 = (c + key) % N
            d2 = (key - c) % N
            dec = (d0, d1, d2)
            for mode in range(3):
                plain = dec[mode]
                freq[mode, plain] += 1
                if p > 0:
                    bg[mode] += good[prev_plain[mode], plain]
                prev_plain[mode] = plain
                if single_flags[p] and (plain == 10 or plain == 24):
                    sh[mode] += 1
        for mode in range(3):
            pair_count = 0
            for j in range(N):
                f = freq[mode, j]
                pair_count += f * (f - 1)
            ioc = N * pair_count / den
            combined = ioc + bg[mode] * 0.1 + sh[mode] / max(singleton_total, 1) * 5
            scores[idx, mode] = combined
            hits[idx, mode] = combined > 3.0
    return scores, hits
