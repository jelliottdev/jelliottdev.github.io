# Do shifted pages produce English?

**Result.** None of **995,724** shifted page-pair readings reaches the fixed English-recognition gate. The strongest score is **−6.4926**, below the gate of **−5.5**. **100 of 128** shuffled searches find an output scoring at least as highly; the plus-one global comparison is **0.783**. These direct shifted sums and differences do not yield a supported English reading.

![The actual strongest English score lies inside the range of shuffled search maxima; known Warning controls score much higher.](experiments/records/lp2-shifted-page-pair-english/english-shift-max.svg)

The [earlier English page-pair test](#/experiments/lp2-page-pair-english) checked only zero-offset alignments. The [shifted difference-IoC test](#/experiments/lp2-shifted-page-pair-differences) added offsets but measured repeated symbols rather than language. This record tests whether shifted arithmetic actually scores like English, using the earlier English record's exact scorer and model.

## The complete bounded grid

We retain the same 55 nonempty LP2-00–55 rune transcriptions and headings. Fifty-two pages have at least 120 runes. Across their **1,326 unordered pairs**, every relative integer shift retaining at least **120 overlapping runes** is tested, without wrapping or repeating either page. The three operations are **A + B**, **A − B** and **B − A**, modulo 29. The two subtraction directions can score differently as English.

There are **331,908 alignments × three operations = 995,724 streams**. Of these, **3,978 zero-offset streams** overlap the earlier English record and match its scores exactly. The remaining **991,746 shifted streams** extend that record's alignment scope. These are settings of one method family, not separate solving ideas.

Each output rune becomes its canonical GP Latin label. The unchanged earlier scorer averages the pinned base-10 English quadgram scores, including the same unseen-group floor, and requires at least 100 Latin quadgrams. Every stream in this minimum-overlap grid qualifies. This is an explicitly English-only model; no missing source language panel was rebuilt or replaced.

The highest observed score is **LP2-13 minus LP2-32 at relative shift 56**, comparing positions 56–176 of LP2-13 with positions 0–120 of LP2-32. That gives 121 output runes and 155 Latin quadgrams. Its score, **−6.4925927**, is not evidence for the stored output as a reading. The complete rune and Latin output is retained in `results.json` for inspection.

## Recovering a known reading first

Before the manuscript search, three planted page pairs use deterministic random keys and the known **184-rune Warning** reading. The second page is constructed so the chosen operation recovers that reading exactly at a nonzero offset: **+1 for the sum, +37 for A − B, and −53 for B − A**.

Each complete planted pair-and-offset search selects the intended reading and operation as its highest score. All three recover every Warning index and score **−4.4784**, above −5.5. Independently shuffling the second page removes the English reading: the resulting complete-search maxima score **−6.6739, −6.9512 and −6.8865**. This demonstrates recovery of the declared direct-English construction at nonzero offsets.

It does not establish sensitivity to every English passage, and it does not show that subtracting two unrelated plaintexts encrypted with a shared key should itself produce English. The tested idea is a direct page-as-pad arithmetic reading, not all possible forms of key reuse.

## Comparing the whole search with shuffled searches

Each of 128 reference trials independently permutes each complete page once, then repeats all 995,724 readings using those shared permuted pages. The permutation preserves each page's rune histogram and length. It destroys word and adjacency structure and does not preserve every particular overlap window's histogram.

The median shuffled maximum is **−6.4486**, slightly higher than the actual best. In 100 trials, the maximum is at least −6.4926; `(100 + 1) / (128 + 1) = 0.78295`. Comparing maxima accounts for choosing the most attractive output anywhere in this declared grid. The −5.5 recognition gate is reported separately and is not treated as a search-adjusted probability threshold.

Shorter overlaps, page reversal, repeated or interrupted page keys, other arithmetic, altered transcriptions, word resets, further decoding layers and other languages remain outside this result. A permutation reference is a structural comparison, not a generative model of LP2.

## Reproduce

The exact grid, scorer, model, plants, shuffle count and seed were frozen before manuscript scoring. A synthetic-only benchmark established that the three-operation grid was modest before the target run. The offline package bundles the prior producer and independent checker source, exact model, GP labels, Warning indices, page arrays, every observed score and all 128 null winners.

```bash
python experiments/records/lp2-shifted-page-pair-english/run.py --check
python experiments/records/lp2-shifted-page-pair-english/check.py
python experiments/records/lp2-shifted-page-pair-english/plot.py --check
```

Python 3, NumPy and Numba are required. The runner regenerates the complete manuscript search and all 128 complete reference searches. The independent checker uses the earlier record's separately written one-stream scorer and its own shifted enumeration. It matches **every observed score exactly**, verifies all 3,978 overlapping baseline scores, independently reruns the planted and shuffled-control searches, and checks every null-winning slice and the global comparison. It does not independently exhaust every alignment within all null trials; the runner provides that complete regeneration.
