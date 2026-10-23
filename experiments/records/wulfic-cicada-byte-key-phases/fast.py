"""Independent compiled implementation of the pinned Stage R phase forward sum.

The state indices stay sorted, so each update merges the stay, advance and
skip streams in one pass.  The source implementation instead calls NumPy's
unique/bincount on every rune.  Both retain the same uniform phase prior,
emission ratio, transition probabilities and relative pruning rule.
"""
from __future__ import annotations

import math
import numpy as np
from numba import njit


@njit(cache=False)
def score(cipher: np.ndarray, key: np.ndarray, ratio: np.ndarray,
          mode: int, shift: int) -> float:
    n, period = len(cipher), len(key)
    capacity = period + 2 * n + 3
    indices = np.empty(capacity, dtype=np.int64)
    weight = np.empty(capacity, dtype=np.float64)
    next_index = np.empty(capacity, dtype=np.int64)
    next_weight = np.empty(capacity, dtype=np.float64)
    count = period
    for j in range(period):
        indices[j] = j
        weight[j] = 1.0 / period
    total = 0.0
    for i in range(n):
        if i:
            at0 = at1 = at2 = 0
            next_count = 0
            while at0 < count or at1 < count or at2 < count:
                left = indices[at0] if at0 < count else capacity + 3
                middle = indices[at1] + 1 if at1 < count else capacity + 3
                right = indices[at2] + 2 if at2 < count else capacity + 3
                position = min(left, middle, right)
                mass = 0.0
                if left == position:
                    mass += weight[at0] * 0.02
                    at0 += 1
                if middle == position:
                    mass += weight[at1] * 0.96
                    at1 += 1
                if right == position:
                    mass += weight[at2] * 0.02
                    at2 += 1
                next_index[next_count] = position
                next_weight[next_count] = mass
                next_count += 1
        else:
            next_count = count
            for j in range(count):
                next_index[j] = indices[j]
                next_weight[j] = weight[j]
        norm = 0.0
        peak = 0.0
        for j in range(next_count):
            k = (key[next_index[j] % period] + shift) % 29
            if mode == 0:
                plain = (cipher[i] - k) % 29
            elif mode == 1:
                plain = (cipher[i] + k) % 29
            else:
                plain = (k - cipher[i]) % 29
            value = next_weight[j] * ratio[plain]
            next_weight[j] = value
            norm += value
            if value > peak:
                peak = value
        total += math.log(norm)
        floor = peak * 1e-12
        count = 0
        for j in range(next_count):
            value = next_weight[j]
            if value >= floor:
                indices[count] = next_index[j]
                weight[count] = value / norm
                count += 1
    return total
