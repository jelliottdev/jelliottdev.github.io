"""Numerical parity with the pinned original scorer, including ties/pruning.

Requires the separately pinned Wulfic checkout. The public numeric profile is
used for real LP2 checks; synthetic inputs exercise equal-mass and strongly
skewed emission states that force many low-mass paths to be pruned.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from check import load_profile, MODES
from fast import score
from replay import source_module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    r, _ = source_module(args.source)
    from tools.lpcore import detect
    keys, ciphers, ratio = load_profile()
    names = sorted(keys, key=lambda name: -len(keys[name]))
    cases = []
    for name in (names[0], names[3], names[10], names[-1]):
        for segment in ("10", "7", "7-15"):
            for mode in MODES:
                for shift in (0, 13, 28):
                    cases.append((f"real:{name}:{segment}:{mode}:{shift}", ciphers[segment], keys[name],
                                  ratio, mode, shift))
    uniform = [1 / 29] * 29
    skewed = [0.98] + [0.02 / 28] * 28
    for name, q, cipher, key in (
        ("uniform-ties", uniform, np.asarray([0, 1, 28, 7] * 40, dtype=np.int64), np.zeros(37, dtype=np.int64)),
        ("skew-pruning", skewed, np.asarray([0, 2, 0, 19, 0, 1, 0, 27] * 130, dtype=np.int64),
         np.asarray([i % 29 for i in range(113)], dtype=np.int64)),
    ):
        sample_ratio = np.asarray(detect.emission_ratios(q), dtype=np.float64)
        for mode in MODES:
            for shift in (0, 13, 28):
                cases.append((f"{name}:{mode}:{shift}", cipher, key, sample_ratio, mode, shift))
    worst = (0.0, "")
    for label, cipher, key, sample_ratio, mode, shift in cases:
        own = score(cipher, key, sample_ratio, MODES[mode], shift)
        # Derive q from ratio: ratio[p] = (1-eps)*29*q[p] + eps.
        q = ((sample_ratio - detect.EPS) / ((1 - detect.EPS) * 29)).tolist()
        source = r.score_cyclic(cipher.tolist(), key.tolist(), q, mode, shift)
        delta = abs(own - source)
        if delta > 1e-8:
            raise AssertionError((label, own, source, delta))
        if delta > worst[0]:
            worst = (delta, label)
    print(f"PASS: {len(cases)} source parity cells, maximum absolute delta {worst[0]:.3g} ({worst[1]})")


if __name__ == "__main__":
    main()
