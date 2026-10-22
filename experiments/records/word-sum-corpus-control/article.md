# How many words fit the selected magic-square totals?

The proposed phrase **PROVE WORTHIER FIND TRUTHS** fits the LP1 square values 131, 151, 151, 131. That arithmetic is already [checked word by word](#/experiments/selected-phrase-word-sums). It leaves a different question: how many *other* words would also fit those values if a solver searched a large list and chose a pleasing phrase afterward?

This control counts candidates in a [preserved revision of the Liber Primus Crib Assist word list](https://github.com/mortlach/Liber-Primus-Crib-Assist/tree/9c10cafce02e512840cc9e173127930594a56281/data/1_grams-full). The supplied discussion linked an older `data/1_grams` path and mentioned a separate `worddata.csv`. Those exact historical bytes are unavailable in the supplied transcript. This is therefore a **pinned-corpus control**, not a reconstruction of every historical search or its dictionary.

## What the census found

The sixteen preserved CSVs contain **138,466 distinct word rows**. Every stored GP total agrees with summing its stored rune values after accounting for one source-font difference: the corpus writes J as `ᛂ`, while this site's manuscript alphabet writes J as `ᛄ`; both carry value 37. The source glyph occurs in 2,217 rows. That mapping is declared in the plan, not silently normalized.

| Phrase slot | Target GP total | Stored rune length | Matching corpus words |
| --- | ---: | ---: | ---: |
| PROVE | 131 | 5 | 38 |
| WORTHIER | 151 | 7 | 15 |
| FIND | 151 | 4 | 10 |
| TRUTHS | 131 | 5 | 38 |

All four proposed words occur in the preserved corpus. At the four fixed totals **and** rune lengths, there are **38 × 15 × 10 × 38 = 216,600 ordered word combinations**. If the first and fourth words must differ, there are **210,900**. These are combinations of dictionary entries, not 216,600 grammatical sentences. They have not been scored for meaning, syntax or relation to the manuscript.

If rune length is discarded, 105 corpus words have GP 131 and 133 have GP 151, giving 195,021,225 ordered combinations for the same four total slots. This illustrates why a claim must state its length constraint before a phrase is chosen. The corpus has only one row with GP 809, **DETECTABILITY** at 13 runes. The proposed **MYRMELEONTIDAE** is absent from this corpus; absence from a bounded word list is not evidence against that separately verified arithmetic assignment.

![Three histograms of corpus word counts by GP sum for four-, five-, and seven-rune words, highlighting the selected 131 and 151 totals.](experiments/records/word-sum-corpus-control/candidate-space.svg)

The graph shows GP totals 80–220 so the selected values remain legible. The downloadable result keeps the complete count distribution for every rune length and observed total. Neither the displayed interval nor the source frequency column is used to select candidate words.

## What was counted

The [plan](experiments/records/word-sum-corpus-control/plan.json) fixes the four word slots, totals and rune lengths. Each distinct CSV row counts once, including rows in the `2a1` and `3a1` files. The script checks the SHA-256 of all sixteen CSVs, the source manifest, its GPL-3.0 license and the manuscript alphabet before reading them. It validates every row's printed GP sum against the stored rune sequence. The opaque source count and flag columns are retained in the output but are not interpreted as independent evidence about language or author intent.

The ordered product lets any word fitting one slot combine with any word fitting the others. It does not test whether a coherent four-word sentence is common. Conversely, finding many alternatives does not prove the proposed phrase accidental. A sentence-level test would need a predeclared grammar or language score, the original vocabulary and all candidate phrases retained, plus matched square-value controls.

## Reproduce

From the repository root or the standalone experiment ZIP, run:

```sh
python experiments/records/word-sum-corpus-control/run.py --check
python experiments/records/word-sum-corpus-control/check.py
```

The runner checks the saved JSON and SVG byte for byte. The separate checker reads the preserved CSVs afresh, verifies each stored GP value and recomputes the target counts and products without importing the runner. Both use Python's standard library and require no network or AI model. The CSVs are redistributed unchanged with their source revision, per-file hashes, attribution and GPL-3.0 text in the experiment bundle.

## Limits and next test

This corpus is a surviving version of the linked tool's word data, not proven identical to the forum attachment called `worddata.csv`. It ends at 14 stored runes and its vocabulary is neither all English nor an unbiased sample of possible keys. The result measures **candidate freedom under one explicit list**. It does not reconstruct how the phrase was selected, apply a word to LP2, or judge any unsolved reading.

The next defensible variant is to recover the historical CSV or document that it is lost, then fix a phrase-generation and scoring procedure before seeing its winners. A separate cipher test must specify which selected word maps to which target, exactly how the word acts as a key, and what held-out output would count as success.
