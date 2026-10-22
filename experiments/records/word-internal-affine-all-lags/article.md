# Affine relations across twelve rune distances

## Finding

Across **12 distances and 841 formulas per distance**, the strongest excess is a **same-rune repeat five positions later**: 102 matches versus 60.6 expected after shuffling runes within each visible word. Only **4 of 999** shuffled-word searches found a result at least this strong (**p = 0.005**, including the one-count Monte Carlo correction). The earlier six-rune rule ranked below this repeat; 23 shuffled searches reached its score somewhere in the full search.

![Histogram of the strongest score in each shuffled-word search, with markers for the actual maximum and the proposed six-rune rule.](experiments/records/word-internal-affine-all-lags/selection-null.svg)

The test finds word-internal structure that this shuffle does not explain. **It does not identify the encryption algorithm.** A shuffle breaks ordinary sequence patterns too, so an elevated count alone cannot distinguish a cipher rule from other structure in the manuscript.

## Why scan the full range?

The [earlier lag-six measurement](#/experiments/word-internal-affine-lags) compared the proposed rule c′ = 24 − 2c (mod 29) against all 841 affine maps **at distance six**. That comparison did not account for choosing the distance after exploration. Here every shuffle must compete over the same 12 distances and 841 maps as the actual transcription. The proposed rule has 77 matches against a shuffle mean of 44.8; its standardized score is 4.763. The complete-search reference reaches at least that score in **23 of 999** trials (corrected tail 0.024). This is a comparison to a wider search, not a fresh independent test of the original idea.

The largest observed score, 5.272, comes from the identity relation at distance five: the rune repeats. It is 102 matches against an exact within-word shuffle expectation of 60.6. Four controls have a maximum score at least this high after repeating the **entire** search. That 4/999 count belongs to the strongest relation, not specifically to the original six-rune formula.

## How the comparison works

Use the archived rune order on LP2-00–55. A hyphen or full stop ends a word; a slash or line break does not. Each page remains separate. For each distance from 1 through 12, count rune pairs that stay within a visible word. Try all maps c′ = ac + b (mod 29), with a and b each 0–28. These are pattern measurements, including noninvertible maps, rather than candidate decryption keys.

For each map and distance, calculate its expected count under independent random order inside each word, keeping that word's exact rune counts. Divide the excess count by the square root of expected count plus one. Select the largest of the **10,092** scores. The denominator is a ranking scale, not a claim that scores follow a normal distribution; the full selection is calibrated by 999 seeded shuffles that repeat the same scan. The [frozen plan](experiments/records/word-internal-affine-all-lags/plan.json) records this score, search range, word rule, seed, stopping rule, and threshold before the run.

## What remains open

The word rule follows the archived transcription, which has disputed separators. Other segmentations, page subsets, relations, and prior exploratory choices were not included in the selection control. The shuffled words preserve local rune counts and word lengths but are not simulated ciphertext. The high same-rune count at distance five should be tested on held-out material or against a more realistic generative control before treating it as a mechanism. Neither result supplies a key, plaintext, or explanation for missing adjacent doublets.

## Reproduce

From the repository root with Python 3.12 and the standard library:

```text
python experiments/records/word-internal-affine-all-lags/run.py --check
python experiments/records/word-internal-affine-all-lags/check.py
```

The first command reruns all 999 complete searches and compares the full [saved result](experiments/records/word-internal-affine-all-lags/results.json) and chart byte for byte. The second independently checks the word and pair counts, the earlier 77-match rule, the exact shuffle expectation on a small exhaustive example, and the saved tail arithmetic. Input hashes and exact bounds are in the plan and download bundle. The run reached its planned 999 trials; the score, range, and stopping rule were not changed after seeing the result.
