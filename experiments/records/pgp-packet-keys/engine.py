"""Numerical GP29 quadgram scorer for finite repeating-byte key phases."""
import numpy as np
from numba import njit, prange

BASE = 26 ** 4


@njit
def score_one(cipher, key, phase, sign, symbols, sizes, weights):
    state = 0
    count = 0
    score = 0.0
    period = len(key)
    for i in range(len(cipher)):
        rune = (cipher[i] + sign * key[(i + phase) % period]) % 29
        for j in range(sizes[rune]):
            state = (state * 26 + symbols[rune, j]) % BASE
            count += 1
            if count >= 4:
                score += weights[state]
    return score / (count - 3)


@njit(parallel=True)
def search(pages, lengths, keyflat, starts, periods, symbols, sizes, weights):
    # One output row per page, phase and sign. Key groups are kept separate.
    total = 0
    for n in periods:
        total += 2 * n
    values = np.empty((len(lengths), total), dtype=np.float64)
    for p in prange(len(lengths)):
        cipher = pages[p, :lengths[p]]
        slot = 0
        for group in range(len(periods)):
            key = keyflat[starts[group]:starts[group] + periods[group]]
            for phase in range(periods[group]):
                values[p, slot] = score_one(cipher, key, phase, -1, symbols, sizes, weights)
                values[p, slot + 1] = score_one(cipher, key, phase, 1, symbols, sizes, weights)
                slot += 2
    return values
