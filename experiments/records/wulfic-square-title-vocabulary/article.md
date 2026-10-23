# Does the LP2-15 number square decode its short heading?

The [LP2-15](#/reader/lp2-15) heading has **two words, four and five runes long**, followed by a 4×4 number square. Wulfic's Stage I asks a narrow question: if the square's construction supplies a nine-number key, can a fixed arithmetic operation turn the **whole heading** into two words in a declared vocabulary?

**Finding:** none of the **30 complete outputs** passes that two-word test. This closes the tested combination of five square-derived number sequences, two reading directions and three arithmetic rules. It does **not** rule out other routes through the square, another spelling convention, or a cipher on the body text.

![The LP2-15 heading tested under five keys, two directions and three operations](experiments/records/wulfic-square-title-vocabulary/comparison.svg)

The five sequences are the printed cell values in the source's spiral order, Fibonacci-indexed primes, those primes minus one, their one-based Fibonacci indices, and the Fibonacci indices themselves. Each is read outward or inward. The first nine values, reduced modulo 29, are applied as ciphertext minus key, ciphertext plus key, or key minus ciphertext. The original **4 + 5 word boundary** stays fixed. The [source-defined vocabulary](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_i.py) uses the solved translation and four pinned English texts, converted to GP rune spellings.

The source also tried **20,000** seeded random nine-rune subtraction keys against the same two-word gate and observed **zero** passes. That is an empirical control, not a zero probability: the vocabulary is a deliberately strict screen, and it cannot by itself decide whether a decoded phrase is meaningful. The [full 30-line source output](experiments/records/wulfic-square-title-vocabulary/source-title-output.txt) shows every complete candidate without selecting attractive fragments.

## Reproduce

The bundled standard-library check independently reads Liberpedia's LP2-15 rune text, reconstructs the Fibonacci and prime sequences, verifies that the sixteen calculated cell values match the printed square's set, and recalculates all **30** outputs:

```text
python experiments/records/wulfic-square-title-vocabulary/run.py --check
python experiments/records/wulfic-square-title-vocabulary/plot.py --check
```

The vocabulary decisions and 20,000-key control come from the pinned source. Recompute them from its original translation and corpora, without copying those texts into Liberpedia:

```text
python experiments/records/wulfic-square-title-vocabulary/replay_source.py PATH_TO_WULFIC_CLONE
```

The wrapper checks the source revision and input hashes, then compares the source output **byte-for-byte**. The [plan](experiments/records/wulfic-square-title-vocabulary/plan.json) records the exact bounds and exclusions.
