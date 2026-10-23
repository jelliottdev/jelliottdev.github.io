"""Finite two-clock GP29 model adapted from one pinned source branch."""
from __future__ import annotations

from collections import Counter

import numpy as np

N = 29


def parse(text: str, alphabet: str, separators: str) -> tuple[np.ndarray, np.ndarray]:
    rune_map = {ch: i for i, ch in enumerate(alphabet)}
    cipher: list[int] = []
    sep_after: set[int] = set()
    for ch in text:
        if ch in rune_map:
            cipher.append(rune_map[ch])
        elif ch in separators:
            sep_after.add(len(cipher))
    prior = np.zeros(len(cipher), dtype=np.int16)
    count = 0
    for i in range(len(cipher)):
        if i in sep_after and i > 0:
            count += 1
        prior[i] = count
    return np.asarray(cipher, dtype=np.int16), prior


def decode(cipher: np.ndarray, prior: np.ndarray, sign: int, letter: int, separator: int) -> np.ndarray:
    positions = np.arange(len(cipher), dtype=np.int16)
    return (sign * cipher + letter * positions + separator * prior) % N


def unique_grid(cipher: np.ndarray, prior: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """All 1,682 effective outputs; source's 5,046 names alias these."""
    positions = np.arange(len(cipher), dtype=np.int32)
    signs = np.repeat(np.asarray([1, -1], dtype=np.int16), N * N)
    letters = np.tile(np.repeat(np.arange(N, dtype=np.int16), N), 2)
    separators = np.tile(np.tile(np.arange(N, dtype=np.int16), N), 2)
    out = (signs[:, None] * cipher[None, :] + letters[:, None] * positions[None, :] + separators[:, None] * prior[None, :]) % N
    return out.astype(np.uint8), np.column_stack((signs, letters, separators))


def normalized_ioc_many(outputs: np.ndarray) -> np.ndarray:
    rows, n = outputs.shape
    if n < 2:
        return np.zeros(rows, dtype=float)
    values = outputs.astype(np.int32) + (np.arange(rows, dtype=np.int32) * N)[:, None]
    counts = np.bincount(values.ravel(), minlength=rows * N).reshape(rows, N)
    return 29 * (counts * (counts - 1)).sum(axis=1) / (n * (n - 1))


def source_score(indices: np.ndarray, ioc: float, bigrams: dict[tuple[int, int], int], trigrams: set[tuple[int, int, int]]) -> tuple[float, int, int]:
    vals = [int(v) for v in indices]
    bg = sum(bigrams.get((a, b), 0) for a, b in zip(vals, vals[1:]))
    tg = sum((a, b, c) in trigrams for a, b, c in zip(vals, vals[1:], vals[2:]))
    return ioc + 0.01 * bg + 0.05 * tg, bg, tg


def source_name_to_effective(direction: str, letter: int, separator: int, mode: str) -> tuple[int, int, int]:
    drift = 1 if direction == "clockwise" else -1
    if mode == "sub":
        return 1, (-drift * letter) % N, (-drift * separator) % N
    if mode == "add":
        return 1, (drift * letter) % N, (drift * separator) % N
    if mode == "beaufort":
        return -1, (drift * letter) % N, (drift * separator) % N
    raise ValueError(mode)


def one_ioc(values: np.ndarray) -> float:
    counts = Counter(int(v) for v in values)
    n = len(values)
    return 29 * sum(v * (v - 1) for v in counts.values()) / (n * (n - 1)) if n > 1 else 0.0
