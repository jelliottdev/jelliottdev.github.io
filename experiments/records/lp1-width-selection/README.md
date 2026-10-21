# Six-width selection: checked research record

Computation and independent replay are complete. The public registry entry, figures and standalone reproduction bundle accompany this record. The protocol was committed as `0aad11d` before new scores were calculated.

## Result

Search widths 2, 4, 8, 16, 32 and 64 in the fixed 464-word object. Each of 49,999 unrestricted word-length permutations receives the same complete search. Select the smallest column imbalance divided by its width-specific permutation expectation (R).

The observed minimum is `4167/245948`, approximately 0.01694, at width **2**. Of the controls, **6,035** have a minimum no greater. The plus-one lower-tail estimate is **0.12072** (`1509/12500`), above the declared 0.05 threshold. This is the outcome for the frozen *minimum-R* selection rule.

| Width | Fixed-width tail, of 49,999 | Unadjusted plus-one estimate |
| --- | ---: | ---: |
| 2 | 6,006 | 0.12014 |
| 4 | 3,429 | 0.06860 |
| 8 | 3,317 | 0.06636 |
| 16 | 54 | 0.00110 |
| 32 | 5 | 0.00012 |
| 64 | 2,044 | 0.04090 |

**Do not describe 0.12072 as an adjustment of the smallest fixed-width p-value.** Width 32 has the smallest diagnostic tail, while width 2 has the smallest R. Dividing by an expectation makes the mean equal across widths; it does not equalize distribution shape or tail probability. Selecting the smallest calibrated tail would be a different statistic and needs its own matched calibration. These six diagnostics are not six independent tests or multiplicity-adjusted results.

The original width-16 exact R and 54/49,999 tail both reproduce. This comparison reuses the baseline's shuffle sequence; it is not independent confirmation. No outcome here removes the original selection of text, boundaries, statistic or candidate widths from the historical exploration.

## Why unequal column sizes need care

Widths 32 and 64 do not divide 464. Retain the partial final row; do not pad it. Let each column contain n_j values, with sum S_j, and let T be the total of n=464 values. Weighted imbalance is Q=sum(S_j²/n_j)−T²/n. Let D=sum(x_i²)−T²/n. Under a uniform permutation, E(Q)=(k−1)D/(n−1).

One derivation uses the population variance v=D/n. Each random column mean is unbiased, with variance v(n−n_j)/(n_j(n−1)). Summing n_j times these variances gives v·n·(k−1)/(n−1), the expectation above. This applies to the declared unrestricted permutation model, not to within-section or sentence-preserving shuffles.

At equal column sizes, the resulting R equals the existing normalized variance of column means. The producer uses nested power-of-two column sums and exact integer score numerators. The independent checker uses direct column slices and rational arithmetic.

## Evidence and reproduction

- Frozen protocol: `experiments/plans/lp1-width-selection.md` and `.json`.
- Producer: `scripts/lp1_width_selection.py`.
- Checker: `scripts/check_lp1_width_selection.py`.
- `results.json`: all six observed scores; every one of 299,994 null width scores; selected minima, ties and tails; plan and source identities.
- `audit.json`: passed independent source reconstruction, explicit Fisher–Yates replay, all width scores, all selected minima/ties and every tail count.

From the repository, using new output paths:

```text
python scripts/lp1_width_selection.py --output width-results.json
python scripts/check_lp1_width_selection.py width-results.json --receipt width-audit.json
```

The checker imports no producer or original word tokenizer. It rebuilds the source lengths with a character scanner and checks the independently computed rational scores against each saved integer ratio. The original observation was already known; no intent, decryption, all-width exclusion or exploration-adjusted discovery claim follows.
