## Does searching other widths change the balance result?

The original comparison arranged 464 word lengths in sixteen columns. This variant asks a different question: if we may choose among six widths, how unusual is the smallest normalized column imbalance we can obtain? Every shuffled control receives exactly the same choice.

The fixed rule selects **width 2**, with normalized imbalance R about **0.01694**. Of 49,999 shuffled controls, 6,035 obtain a minimum no greater. The plus-one lower-tail estimate is **0.12072**, above the declared 0.05 threshold. This test does not support an unusually small minimum-R under its unrestricted-shuffle model.

That conclusion needs a precise qualification: **this is not an adjustment of the smallest fixed-width p-value**. Width 32 has the smallest unadjusted tail in the table below; width 2 has the smallest R. Choosing between those criteria after seeing the results would change the experiment.

## What is fixed, and what changes?

Use the same Warning, Welcome, first koan and second koan as the [464-word baseline](#/experiments/lp1-word-length-balance). Keep their order, headings, interruption runes, word boundaries and internal apostrophes. Count native runes per word. The source population contains 464 words and 1,796 runes.

Try only widths **2, 4, 8, 16, 32 and 64**. Word i, counted from zero, goes in column i modulo the width. Do not rotate the start, reorder sections or pad the final row. Widths 32 and 64 leave unequal column sizes, so the statistic explicitly weights by the number of words in each column.

The width set follows the earlier power-of-two discussion, including 64. The original width-16 result and qualitative observations about other widths were known before this protocol. The protocol was committed before these new measurements; that does not erase the earlier exploration.

## Why divide by an expectation?

Let n be the number of words, T their total length, n_j the size of column j and S_j its length sum. Define weighted imbalance as Q = sum(S_j² / n_j) − T² / n. Lower Q means more similar column means. Let D = sum(x_i²) − T² / n, where x_i is each word length.

Under an unrestricted permutation of those fixed lengths, the expected Q for k columns is (k−1)D/(n−1). We use **R = Q / expected Q**. At width 16, this equals the baseline's normalized variance of column means. The derivation and exact arithmetic are preserved in the research README.

Dividing by the expectation makes the mean equal to one under each width's null distribution. It does **not** make those distributions have the same shape. An R of 0.02 at one width can be less unusual than an R of 0.3 at another. The declared selection rule nevertheless chooses the minimum R, and its control distribution must repeat precisely that rule.

## Every tested width

The fixed-width tails below include ties and use the plus-one correction. They are diagnostic, unadjusted comparisons—not independent evidence or six corrected tests.

| Width | Words per column | Observed R | Fixed-width tail / 49,999 | Unadjusted estimate |
| --- | --- | ---: | ---: | ---: |
| 2 | 232 | 0.01694 | 6,006 | 0.12014 |
| 4 | 116 | 0.14684 | 3,429 | 0.06860 |
| 8 | 58 | 0.34531 | 3,317 | 0.06636 |
| 16 | 29 | 0.25150 | 54 | 0.00110 |
| 32 | 14 or 15 | 0.31188 | 5 | 0.00012 |
| 64 | 7 or 8 | 0.73060 | 2,044 | 0.04090 |

The width-16 exact R and 54-control tail reproduce the original baseline. The same random seed and fresh-copy shuffle sequence are used, so this agreement is a reproduction check, not an independent replication.

## Matching the selection in every control

Generate 49,999 unrestricted permutations using Python's Random with seed 330146. For each one, calculate all six R values and retain the minimum, including every tying width. Compare those minima with the observed minimum using exact rational arithmetic. The result is (6,035 + 1)/(49,999 + 1) = **0.12072**.

The null figure includes all controls. Its bins are for display only; the tail count uses the exact values, not histogram bins. The saved report retains all 299,994 null width scores, their minima and ties.

This does not account for every width, every possible grouping of text, the original selection of the 464-word object, or choosing the statistic itself. It also does not preserve coherent sentences or each section's length distribution in the controls. The [within-section variant](#/experiments/lp1-section-balance) and [section-order variant](#/experiments/lp1-section-order) address different choices. No result here identifies a grille or the unsolved cipher.

## Reproduce and inspect

Download this experiment's ZIP and extract its folders. Python 3's standard library is sufficient; the bundle includes the source transcriptions and baseline dependencies. No network access, API or model is used.

```text
python experiments/records/lp1-width-selection/run.py --check
```

To retain a fresh replay instead of using a temporary directory:

```text
python experiments/records/lp1-width-selection/run.py --output my-width-replay
```

The producer reconstructs the baseline words and scores nested power-of-two columns with exact integer ratios. The independent checker imports neither the producer nor its word tokenizer: it scans the source characters, explicitly replays Fisher–Yates and calculates each Q from direct column slices with rational arithmetic. It checks all observed scores, all 299,994 null scores, minima, ties and tail counts. Both computations agree; human review remains pending.
