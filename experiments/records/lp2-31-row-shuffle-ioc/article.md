# LP2-31 periodic IoC: preserving row composition

## Why change the null model?

The baseline shuffles all 269 runes together. That preserves the page's total counts but can move any rune to any row. If rows differ in composition, that comparison removes those differences as well as the ordering under investigation.

This variant instead preserves each archived row's length and exact rune counts, shuffling only within that row. It asks a conditional question about order after holding row composition fixed. This is not automatically a better model; it makes a different assumption visible.

LP2-31 has twelve ordinary text rows and no separately identified heading. No row was removed or renamed as a heading for this test. Archived transcription lines provide the boundaries.

## Plan and relation to the baseline

The plan and runner were committed as `8dfc7c0` before executing the variant. The variant was motivated after the whole-page result was known; it is not independent confirmation and does not account for selecting among null models.

Only the shuffle procedure changes. The input remains the same 269 runes, periods remain 2–20 inclusive, the statistic remains pooled within-column matching pairs, and each trial's maximum is compared with the observed maximum. There are still 999 trials, seed 330131, greater-than-or-equal ties, plus-one Monte Carlo correction, and a 0.05 threshold.

The twelve row lengths are:

```
23, 22, 24, 24, 22, 22, 21, 22, 21, 24, 22, 22
```

Remove non-alphabet characters inside each row, shuffle that row's runes, then concatenate rows in their original order. Column positions run across the concatenated page; they do not restart at row boundaries. The same seed does not make the two models' individual shuffled pages equivalent or create a paired statistical test.

## Results

| Quantity | Whole-page baseline | Within-row variant |
| --- | --- | --- |
| Input runes | 269 | 269 |
| Observed peak period | 13 | 13 |
| Observed peak fraction | 216/5300 | 216/5300 |
| Null maxima at least observed | 213/999 | 245/999 |
| Plus-one Monte Carlo p | 0.214 | 0.246 |
| Below declared 0.05 threshold | No | No |

The observed scores agree exactly for every period, as they should: the observed input and scoring procedure did not change. The within-row comparison is 246/1000 = 0.246. Its approximate Monte Carlo standard error is 0.014, using sqrt(q*(1-q)/999) with q=245/999. This describes simulation uncertainty, not confidence in a cipher.

The two runs give the same threshold decision under their different assumptions. The difference between 0.214 and 0.246 is not evaluated as a separate statistical effect, and neither p-value is the probability that period 13 is the true key length.

## Reproduce

From a repository checkout with Python 3.12.10:

```
python experiments/records/lp2-31-row-shuffle-ioc/run.py --check
python experiments/records/lp2-31-row-shuffle-ioc/check.py
```

The runner compares every observed field and all 999 stored trial records. The separate checker verifies the twelve row lengths, exact agreement with the baseline's observed scores, and a position-pair oracle for all observed periods and the first three seeded null trials. That oracle directly enumerates position pairs rather than using column-frequency counts. The runner also asserts preservation of each row's multiset in every trial.

[Download the complete variant output](experiments/records/lp2-31-row-shuffle-ioc/results.json). All 19 period numerators are stored for every shuffle; the denominators are in the observed rows. The comparison diagram is generated from the two saved reports. Neither the checker nor the plot interprets candidate plaintext or calls an AI service.

## Retest and changes after inspection

Codex reran the complete variant and performed the separate checks on 20 October 2026. Every stored field reproduced. No null rule, period range, input boundary, seed, threshold or statistic changed after the variant's first result. The checker and comparison graphic were added afterward for verification and presentation. Human review remains pending.

## Interpretation and remaining limits

This row-conditioned null preserves more local composition than the whole-page null, but still discards within-row word boundaries and local patterns. It treats all rune permutations within a row as exchangeable. Neither model is a full model of a particular cipher or language.

This variant does not show that the page is random, that period 13 is impossible, or that Vigenère is absent. It also does not test different pages, period ranges, row selections, alternative statistics or key searches. Those changes must be documented separately rather than silently folded into this result.
