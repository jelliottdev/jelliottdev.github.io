## Finding

We tested whether the 256-byte number-grid payload could supply a **rune-by-rune key** for Liber Primus. In this fixed 32-case screen, **none passed** the source's English-score threshold. The best candidate scored **−7.105**, below both the required **−5.5** and the highest of 200 shuffled-text controls (**−7.001**). A higher score is better.

![Scores for planted controls, the best manuscript candidate, the shuffled-text ceiling and the required threshold.](experiments/records/grid-payload-prf-seed-corner/score-comparison.svg)

The decoder was capable of recognizing a supplied key. Four planted controls, one per generator, recovered **98.9%** of characters and scored **−4.17**. This makes the negative result meaningful for the fixed cases below; it does not prove the payload has no role elsewhere.

## What was tested

The [pinned B-05 source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round13/B05/PREREG.md) supplies two 256-byte readings of the number grid. Each was used directly as a seed for SHA-256 counter mode, RC4, HMAC-DRBG-SHA256 or AES-256-CTR. For each generator we tried both byte-to-rune reductions and both addition signs: **2 × 4 × 2 × 2 = 32** keys. The source's skip-aware beam decoded the first 400 unsolved runes with a forward key starting at offset zero.

This is a deliberately small corner of B-05, whose published search also included transformed payloads, more generators, reverse keys, Atbash, offsets, and contested-byte variations. We did not revalidate that whole published sweep here. Nor does an English-scoring failure exclude non-English plaintext or a different way to use the grid.

## Reproduce

The [saved result](experiments/records/grid-payload-prf-seed-corner/results.json) lists all 32 scores. From the repository root, install Python 3 and `cryptography`, then run:

```text
python experiments/records/grid-payload-prf-seed-corner/run.py --check
python experiments/records/grid-payload-prf-seed-corner/check.py
```

The first command reruns the four planted controls, 200 shuffles and 32 candidates using bundled pinned source in a temporary folder. The second checks the case grid, threshold, payload hashes and independent PRF spot checks. The [source manifest](experiments/records/grid-payload-prf-seed-corner/source-manifest.json) pins each upstream file by Git blob and SHA-256; the source is bundled under its MIT license.
