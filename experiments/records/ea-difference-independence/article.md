# Are the nonzero differences independent under the EA-stalling model?

The [EA-frequency control](#/experiments/ea-frequency-control) compared the 86 LP2 doublets with decoded GP EA on solved pages and examined the index of coincidence (IoC) of successive ciphertext differences. This companion check asks what the **specific independent-nonzero-key version** of that equation predicts beyond the zero count. It keeps the observed zero positions and page boundaries fixed; it does not search for plaintext or keys.

Under `Cᵢ = Cᵢ₋₁ + Kᵢ(Pᵢ − 28) mod 29`, with each key independently uniform on 1–28 and independent of a fixed plaintext, every plaintext EA gives difference zero. For any other plaintext rune, multiplication by its nonzero offset permutes 1–28. Therefore, **conditional on the zero mask**, the other differences must be independent uniform draws from those 28 residues. This is a prediction of the declared key model, not of every running-sum cipher. A periodic, deterministic or nonuniform key need not have it.

![Counts of the 28 nonzero difference residues on LP2-00–55, with their equal-count reference marked in red.](experiments/records/ea-difference-independence/differences.svg)

## Input and two diagnostics

Read archived LP2-00–55, including headings. Retain the 29 GP runes, discard other characters, and subtract each previous rune index from the next **within the same page** modulo 29. There are 12,901 differences: **86 zero** and **12,815 nonzero**. No pair is formed across a page boundary. The zero mask remains at its observed positions in all simulations.

The first diagnostic is the Pearson chi-square of the 28 nonzero residue counts against an equal-count reference. The expected count per residue is **12,815 / 28 ≈ 457.68**. The second counts equal neighboring nonzero differences. Both difference positions must be consecutive within one page; a zero between them breaks the comparison. That leaves **12,676 eligible pairs**, with **452.71** expected equalities if the nonzero draws are independent uniform residues.

| Diagnostic | Observed | Central 95% of 2,000 conditional draws | Draws at least observed |
| --- | ---: | ---: | ---: |
| 28-bin Pearson chi-square | 42.056 | 14.403–43.092 | 69 / 2,000 |
| Equal neighboring nonzero differences | 432 / 12,676 | 412–492 | 1,685 / 2,000 |

The histogram statistic is near the high end of this seeded conditional reference. The order-sensitive count sits within it. The simulation uses seed `33012026`; every trial fills only nonzero-mask slots with independent draws from 1–28. In a positive control, those synthetic differences were accumulated into ciphertext and differenced again, recovering the simulated values exactly. The complete result stores all 28 observed bins, both tails of each simulated rank, source hashes and the plan.

## The histogram is not independent evidence from the previous IoC

Let `m = 12,815` and let `c₁ … c₂₈` be the nonzero difference counts. The chi-square is `28 Σ cᵣ² / m − m`. With the **86 zero differences fixed**, the full difference IoC has numerator `86 × 85 + Σ cᵣ(cᵣ − 1) = 86 × 85 + Σ cᵣ² − m` and a fixed denominator `12,901 × 12,900`. Both statistics are increasing functions of the same `Σ cᵣ²`. They rank every conditional simulated histogram in exactly the same order. The histogram makes the individual residues inspectable; its 69/2,000 upper rank is **not a second independent hint** alongside the earlier IoC result.

Neighboring equality instead uses the **order** of nonzero differences. A page can keep every residue count—and thus the chi-square and IoC—while a rearrangement changes this adjacent-pair statistic. Here 432 equalities are below the 452.71 uniform expectation but inside the simulated central range. It would be a mistake to infer a periodic key, or its absence, from this one lag-one check.

## What the result leaves open

The model and diagnostics were selected after the low doublet count and difference IoC were already known. These inclusive Monte Carlo ranks are descriptive and unadjusted for that selection or for examining two related summaries. They do not provide a prospective probability that the manuscript uses this cipher. A near-uniform residual distribution is compatible with many mechanisms; a small departure would challenge only the independently uniform nonzero-key version under these boundaries and transcription choices.

No plaintext EA positions have been verified, no key has been recovered, and no unknown page has been read. A deterministic key schedule, a clock that pauses on EA, word or page resets, changed rune mapping, and alternate transcription layers require separately declared tests. See the [doublet guide](#/wiki/doublets?section=ea-constraint) for the algebra and the [placement audit](#/experiments/doublet-placement) for the spatial distribution of the 86 zeros.

## Reproduce

Extract this experiment's ZIP without flattening folders. Python 3.12 and its standard library suffice:

```text
python experiments/records/ea-difference-independence/run.py --check
python experiments/records/ea-difference-independence/check.py
```

The producer reruns the 2,000 conditional draws and checks the saved JSON and SVG byte for byte. The independent checker extracts the Runic Unicode block with a different parser, verifies every source hash, recomputes the 28 bins and adjacent statistic, and calculates chi-square from an exact rational formula. Both use archived text, not a fresh manual rereading of the JPEGs. The [test plan](experiments/records/ea-difference-independence/plan.txt), [result data](experiments/records/ea-difference-independence/results.json) and [figure](experiments/records/ea-difference-independence/differences.svg) are available separately.
