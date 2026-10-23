# Where could a repeat filter act?

LP2-00–55 contains **86 equal adjacent rune pairs among 12,955**. One [published seven-model comparison](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L2-filter-leak) asks whether that scarcity looks like a filter on the output, the key, or the input text. We reproduced its complete 200-replicate simulation and saved every result field.

## Finding

![The observed repeat rate is 0.664 percent. Key skip and output rewrite are near it; fixed nudge also matches repeats but fails another statistic. No filter, key filter and text filter are around 3.5 percent; hard ban produces zero.](experiments/records/r18-filter-locus-replay/filter-loci.svg)

Two **output-stage** models reproduce the observed repeat rate within this setup: discard a key draw and retry (**0.633%** simulated), or overwrite a repeated output with a fresh random rune (**0.668%**). The manuscript has **0.664%**. The source's classifier has only **17.5% in-sample power** to distinguish the rewrite model from key skipping at its stated 5% false-positive threshold. That is weak separation, not evidence that either mechanism was used.

A third output rule—always nudging a repeated rune by one—also matches the repeat count (**0.659%**). But it makes one modular rune-to-rune difference far too common: its mean largest standardized deviation is **16.5**, versus **2.64** in the manuscript. The unfiltered, key-filtered, and plaintext-filtered source models leave roughly **3.5%** adjacent repeats. A hard output ban leaves **zero**. Those are mismatches for these precisely defined models, not exclusions of every possible filter or cipher.

## What this test actually compares

Each model encrypts the same Gematria Primus encoding of a pinned King James Bible text using simulated uniform 29-value key draws. Where the model has a suppression parameter, the source tunes it to the manuscript's repeat rate before measuring 200 seeded streams of 12,956 runes. Five preselected measurements then include adjacent repeats, other short-distance repeats, alternation, and the distribution of modular differences. The complete [source output](experiments/records/r18-filter-locus-replay/source-results.json) and our [replayed output](experiments/records/r18-filter-locus-replay/replayed-results.json) match in **every field except elapsed time**. These linked copies encode the source's infinite hard-ban deviation as `null`; the exact [source bytes](experiments/records/r18-filter-locus-replay/source-output-raw.txt) are preserved separately.

The source fits each classifier's means, spreads, and threshold on those same simulated streams used to report power. Its **17.5%** and **100%** figures are therefore *in-sample discrimination within this seven-model comparison*, not held-out performance. The manuscript's repeat rate is also used to tune some models; matching that same rate cannot validate a model. Our separate [probability-law check](#/experiments/rejection-channel-information) shows why idealized key-skip and fresh-random-output rules can have the same visible ciphertext distribution. This simulation does not identify which, if either, produced LP2.

## Reproduce

The ZIP includes the exact [KJV input](exports/sources/gutenberg-10-kjv.txt), preserved from [Project Gutenberg](https://www.gutenberg.org/files/10/10-0.txt). The runner verifies its hash; the source-code checkout and NumPy are still required.

The [frozen plan](experiments/records/r18-filter-locus-replay/plan.json) pins source revision `f08b20b`, exact code and input hashes, the 200-replicate command, and the preserved result hash. Use a checkout of that revision and the exact `kjv.txt` named in the plan. With the source repository at `SOURCE`:

```text
python experiments/records/r18-filter-locus-replay/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --check
python experiments/records/r18-filter-locus-replay/check.py
python experiments/records/r18-filter-locus-replay/plot.py --check
```

The runner verifies SHA-256 inputs, stages only the required source files in a temporary directory, and runs the source there, leaving its tracked result file untouched. NumPy is needed for the source simulation. The independent checker uses the repository's LP2 transcription to recount the **27 manuscript measurements** and the conditional draw-count arithmetic; it does **not** independently re-estimate the source classifier's power.
