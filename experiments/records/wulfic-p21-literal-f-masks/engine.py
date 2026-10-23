"""Exact finite source F-mask selector, with a compiled all-mask scan."""
from __future__ import annotations

import ast

import numpy as np
from numba import njit

RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
SEPS = set(".-• \n")


def source_weights(source_bytes: bytes) -> np.ndarray:
    """Read the literal bigram table in the pinned source, including overrides."""
    tree = ast.parse(source_bytes.decode("utf8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "score_text")
    mapping = next(ast.literal_eval(n.value) for n in fn.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "bigrams" for t in n.targets))
    out = np.zeros((29, 29), dtype=np.int32)
    for (a, b), weight in mapping.items():
        out[a, b] = weight
    return out


def parse_page(raw: str) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Copy source load_page_raw's rune and word-separator policy."""
    vals = []
    word_lengths = []
    current = 0
    for ch in raw:
        if ch in RUNES:
            vals.append(RUNES.index(ch)); current += 1
        elif ch in SEPS and current:
            word_lengths.append(current); current = 0
    if current:
        word_lengths.append(current)
    singleton = np.zeros(len(vals), dtype=np.uint8)
    pos = 0
    for length in word_lengths:
        if length == 1:
            singleton[pos] = 1
        pos += length
    assert pos == len(vals)
    return np.asarray(vals, dtype=np.int16), singleton, word_lengths


@njit(cache=True)
def scan_masks(cipher: np.ndarray, key: np.ndarray, mode: int, singletons: np.ndarray,
               weights: np.ndarray) -> tuple:
    n = len(cipher)
    f_bit = np.zeros(n, dtype=np.int32)
    f_count = 0
    for i in range(n):
        if cipher[i] == 0:
            f_bit[i] = 1 << f_count
            f_count += 1
    assert f_count <= 16
    n_single = 0
    for i in range(n):
        n_single += singletons[i]
    gated_count = 0
    best_score = -1.0
    best_score_mask = -1
    best_ioc = -1.0
    best_ioc_mask = -1
    baseline_ioc = -1.0
    baseline_bg = -1
    best_score_ioc = -1.0
    best_score_bg = -1
    for mask in range(1 << f_count):
        freq = np.zeros(29, dtype=np.int32)
        ki = 0
        prev = -1
        bigram = 0
        passing = True
        for i in range(n):
            if f_bit[i] != 0 and (mask & f_bit[i]) != 0:
                p = 0
            else:
                k = key[ki % len(key)]
                if mode == 0:
                    p = (cipher[i] - k + 29) % 29
                elif mode == 1:
                    p = (cipher[i] + k) % 29
                else:
                    p = (k - cipher[i] + 29) % 29
                ki += 1
            freq[p] += 1
            if prev >= 0:
                bigram += weights[prev, p]
            prev = p
            if singletons[i] and p != 10 and p != 24:
                passing = False
        collisions = 0
        for v in freq:
            collisions += v * (v - 1)
        ioc = 29.0 * collisions / (n * (n - 1))
        if mask == 0:
            baseline_ioc = ioc
            baseline_bg = bigram
        if ioc > best_ioc:
            best_ioc = ioc
            best_ioc_mask = mask
        if passing and n_single > 0:
            gated_count += 1
            score = ioc * 100.0 + bigram * 0.5
            if score > best_score:
                best_score = score
                best_score_mask = mask
                best_score_ioc = ioc
                best_score_bg = bigram
    return (f_count, n_single, gated_count, baseline_ioc, baseline_bg,
            best_score, best_score_mask, best_score_ioc, best_score_bg,
            best_ioc, best_ioc_mask)


def mask_positions(cipher: np.ndarray, bits: int) -> list[int]:
    return [int(i) for j, i in enumerate(np.flatnonzero(cipher == 0)) if bits >= 0 and (bits >> j) & 1]
