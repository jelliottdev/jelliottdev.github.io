## Finding

The number grid on pages 49–51 can be read as a 256-byte payload. Six byte positions have two documented readings. We tried **every combination of those readings** as the seed of a rune-by-rune key. Across the source's **3,840 decoder calls**, no candidate reached its predeclared English-score threshold. The best score was **−6.872**; the required score was **−5.5**. Higher is better.

![The best payload-derived candidate, source shuffled-text reference, planted control and required threshold.](experiments/records/grid-payload-prf-contested-masks/result-score.svg)

This screen was able to find a key when one was planted. We extended the source's recovery control to all **15 generators with both byte-to-rune reductions**: all **30** met its four recovery gates. That supports the negative finding for this bounded test, not a claim about every possible use of the grid.

## What the search covers

Each of the six uncertain bytes took one of its two recorded values: **2⁶ = 64 payloads**. The [pinned B-05 source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round13/B05/sweep.py) expanded each payload with 15 pseudorandom generators, two ways to turn bytes into rune values, and both addition signs. It used a skip-aware decoder on the **first 400 runes** of the unsolved text (LP2-00 and the beginning of LP2-01). The key ran forward from offset zero, without Atbash.

The 3,840 calls contain **2,596 distinct key/sign cases**. AES-128-CTR uses only the first 16 payload bytes, so none of the six contested positions can change its key. Four AES-256/ChaCha variants use only byte 25 among those six. The remaining ten generators respond to all 64 readings.

![How many distinct keys each generator group produces from the 64 candidate payloads.](experiments/records/grid-payload-prf-contested-masks/key-sensitivity.svg)

The source's 200 shuffled-text scores provide a reference, but their maximum is **not** a chance threshold adjusted for choosing the best of 3,840 calls. The fixed −5.5 English-score requirement is the decisive boundary here. This record covers B-05's **Part 2a**, not its larger main grid, single-byte-all-values sweep, other offsets, full-page reruns, or non-English readings.

## Reproduce

The [complete score list](experiments/records/grid-payload-prf-contested-masks/cases.json), [summary](experiments/records/grid-payload-prf-contested-masks/results.json), and [key-equivalence count](experiments/records/grid-payload-prf-contested-masks/key-equivalence.json) are saved. From the repository root, use Python 3 with `cryptography`:

```text
python experiments/records/grid-payload-prf-contested-masks/run.py --check
python experiments/records/grid-payload-prf-contested-masks/control-all.py --check
python experiments/records/grid-payload-prf-contested-masks/key-equivalence.py --check
python experiments/records/grid-payload-prf-contested-masks/check.py
```

The first command replays all 3,840 source-defined calls and takes several minutes. The other commands check the 30 planted controls, the effective-key duplicates, complete case coverage, and the 32 scores that overlap the earlier raw-payload test. Source code and bytes are bundled from the pinned MIT-licensed repository.
