# Could a mathematical sequence be the LP2 key?

**The specified number streams did not produce a reading under the tested model.** We replayed two public experiments that turn mathematical sequences into GP29 key values: fixed constants and concatenated numbers in [Stage AG](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ag.py), and arithmetic functions in [Stage AH](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ah.py). **None of the 19,140 scored settings met the source's reading threshold.** All 594 adequately long stream/alignment/mode groups met its exclusion rule. The remaining 66 groups use only *nine runes* from section 10, so they cannot settle much.

![No tested setting reached the reading threshold; the only undecided groups use nine runes.](experiments/records/wulfic-number-key-streams/comparison.svg)

## The tested keys

Stage AG uses base-29 digits of π, e, φ, √2, √3, ln 2 and √3301, plus concatenated primes, positive integers and prime totients. Stage AH uses φ(n), divisor sums, cumulative totients, prime gaps, φ(φ(n)) and nφ(n), each directly and as a running sum, reduced modulo 29. That gives **22 named streams, 21 distinct streams**: the running sum of φ(n) is the same sequence as the direct cumulative-totient stream.

The source reads each key from one of **1,000 possible starting positions**, allowing occasional stays and skips so a small alignment error need not destroy a genuine signal. It tests three arithmetic directions and all 29 shifts on sections 7–15 individually, then on their joined stream. Its score asks whether the resulting rune frequencies look more like the solved LP1 readings than a flat-rune reference. The [frozen plan](experiments/records/wulfic-number-key-streams/plan.json) gives the exact settings and input hashes.

The source set **+30** as its reading threshold. For groups long enough to judge, the best score was **−47.85**, on section 7 using the running sum of φ(φ(n)); a positive score this far away was never reached. The best score over *all* settings was only **+1.76**, on section 10's nine runes. The source's exclusion criterion requires **all 29 shifts in a group to score at most −10**, with its planted controls working. It holds for every group outside that short section: **270/300** Stage AG groups and **324/360** Stage AH groups. The groups are model settings, not separate proposed solutions.

## Why the check is credible—and limited

For each named stream, the pinned program planted a known-key encryption at both 729 and 3,316 runes, with two key-continuation rules. All **88 positive controls** exceeded +30; the corresponding wrong-key controls stayed below it. We ran the complete source programs and compared all four [candidate and control tables](experiments/records/wulfic-number-key-streams/results.json) byte-for-byte with the published tables. An [independent check](experiments/records/wulfic-number-key-streams/check.py) rebuilds the 12,956-rune manuscript stream from Liberpedia's page files, checks the full parameter grid and controls, and verifies small arithmetic prefixes and the duplicate sequence.

This result concerns these **particular base-29 streams and the source's drift-tolerant frequency model**. It does not reject other numerical keys, different ways to turn a constant into runes, different boundaries or a cipher with a different plaintext distribution. Nor does a failure to reach the reading threshold establish that the manuscript was not constructed with mathematics.

## Reproduce

From the repository root, run `python experiments/records/wulfic-number-key-streams/run.py --check` and `python experiments/records/wulfic-number-key-streams/check.py`. The full upstream rerun needs a separate checkout of [Wulfic's repository](https://github.com/Wulfic/Cicada3301-Liber_Primus) at commit `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`, with its Python dependencies installed; run `python experiments/records/wulfic-number-key-streams/replay_source.py --source-dir PATH_TO_CLONE`. That wrapper checks the pinned source files, runs both stages into a temporary folder and compares their complete output tables with this archive.
