# Do named keyword alphabets fit LP2?

Wulfic's Stage V builds substitution alphabets from **34 specified words and phrases**, including `DIVINITY`, `KNOW THIS`, `CICADA`, and the known parable. After collapsing duplicates, those give **68 distinct alphabets**. The test checks every source-defined choice of plaintext, ciphertext and key alphabet for each of six key-value distributions. It scores **whole LP2 rune frequencies**; it does not assemble or read a plaintext sentence.

**Finding:** the source's calibration gate passes, but **no tested member reaches its +10 lead threshold**. For English-rune, prime-value, English Latin-letter and decimal-digit key distributions, every named-alphabet combination is both control-powered and below the source's −10 exclusion cutoff. Hexadecimal digits leave **135** powered combinations above that cutoff; uniform A–Z leaves **10,197**. Neither group supplies a reading or a positive lead. Many A–Z combinations lack enough control power, so they remain untestable.

![Control-qualified outcomes for six named-alphabet key distributions](experiments/records/wulfic-keyword-quagmire-models/comparison.svg)

Each family has **314,432 alphabet combinations**. That is the size of one bounded search, **not** a count of independent solving ideas. The chart shows the share of each family that is both below the exclusion cutoff and powerful enough to judge, above the cutoff with power, or untestable. Hexadecimal's 135 powered survivors are too small to distinguish at the chart's scale; their exact count remains in the data.

## How the screen works

The source considers an identity alphabet and each keyword alphabet or its inverse. It combines three of those alphabets, tries its three arithmetic sign modes and all 29 constant offsets, then keeps the best **single-rune frequency** score for each combination. Six declared key-value distributions come from English runes, their prime values, English Latin letters, decimal digits, hexadecimal digits and uniform A–Z letters.

Before looking at LP2, the source tested **50 generated messages per family** under their own model; none fell below the −10 cutoff. For each alphabet combination, at least **18 of 20** flat-key controls must fall below the cutoff before a low LP2 score counts as a *powered exclusion*. The source's raw “excluded” count also includes some combinations without that power. We keep those in the untestable part of the chart. This distinction matters especially for uniform A–Z.

The [source result table](experiments/records/wulfic-keyword-quagmire-models/source-stage_v_results.tsv) contains the gate results, six family summaries, and **10,332** listed powered non-exclusions. Those listings are candidates within this frequency screen, not decoded messages. The highest LP2 score is **+6.51**, below the source's +10 lead rule. A different keyword set, a non-independent key sequence, another alphabet construction, page-specific resets or layered encryption remains outside this test.

## Reproduce

The bundled checker independently counts the **12,956** LP2 runes from Liberpedia's page files, audits all source gate and family summaries, and checks every listed survivor against its cutoff and power label:

```text
python experiments/records/wulfic-keyword-quagmire-models/run.py --check
python experiments/records/wulfic-keyword-quagmire-models/plot.py --check
```

We also reran the [pinned source program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_v.py): all **10,357 rows match its published table byte-for-byte**. The [plan](experiments/records/wulfic-keyword-quagmire-models/plan.json) fixes its inputs, key rules and thresholds. With a matching external checkout and NumPy, repeat that source computation in a temporary output file:

```text
python experiments/records/wulfic-keyword-quagmire-models/replay_source.py PATH_TO_WULFIC_CLONE
```
