## What was tested

The archived LP2-00–55 text has **86 adjacent equal-rune pairs across 12,901 within-page edges**. Independent uniform additive keys modulo 29 would produce about **444.86 matches on average**. The exact probability of 86 or fewer under that model is approximately **1.0708 × 10⁻⁹⁸**.

This is a strong disagreement with one precisely defined model. It does not rule out encryption, random choices in other constructions, or any particular plaintext language. The low count and an earlier statement of this model were known before the replication. The probability is conditional on the model and is not adjusted for the historical search across manuscript features.

## The model in ordinary terms

For every plaintext rune, independently choose a key uniformly from 0 through 28 and add it modulo 29. The plaintext may be any fixed sequence. Each resulting ciphertext rune is uniform, and different positions are independent. Keep the observed page lengths fixed.

The prediction concerns fresh, independent uniform symbols. A shuffle that preserves the manuscript's observed rune counts asks a different question. So does a generator that forbids repeats, uses nonuniform keys, reuses key values dependently, or changes its output according to the plaintext.

The [EA running-sum control](#/experiments/ea-frequency-control) examines an especially different equation: nonzero multiplicative keys and an EA offset make repeats depend on plaintext EA frequency. Its required EA count should not be tested with this record's independent-uniform-additive-key tail.

The [short-lag profile](#/experiments/doublet-lag-profile) uses that different, fixed-count page-shuffle reference. It shows the deficit at adjacent positions but not at rune distances two through five. Its bands must not be read as the exact uniform-key probability computed here.

## Why overlapping pairs still give a binomial law here

Adjacent comparisons share positions: the first pair of ABC uses A and B, and the next uses B and C. Shared positions do not automatically make these match indicators dependent under this particular uniform model.

Within one page, replace the ciphertext sequence by its first rune and the successive differences modulo 29. This transformation is reversible: start at the first rune and add each difference to recover the page. A reversible transformation of the uniformly distributed full sequence remains uniform over all such coordinate tuples. The differences are therefore independent uniform residues. A pair matches exactly when its difference is zero, which has probability 1/29.

Apply this separately to each page. There are 12,956 runes on 55 nonempty pages, hence **12,956 − 55 = 12,901 differences**. LP2-50 has no alphabet runes and adds no edge. Their zero count has the binomial distribution with 12,901 trials and success probability 1/29.

Uniformity matters. For independent binary symbols with probabilities 3/4 and 1/4, one pair matches with probability 5/8. Both overlapping pairs match with probability 7/16, which is different from (5/8)² = 25/64. The corresponding independence argument fails for that nonuniform model.

## Reading the figure and the probability

The bars show probabilities for ten-count intervals under the uniform model. The observed count is far to the left of the main mass; its tiny probability cannot be resolved at this linear plotting scale. Values 650 and above are retained in one overflow bin in the JSON but omitted from the displayed range. The exact lower tail includes every count from zero through 86, not just the probability of exactly 86.

The numerator is the integer sum `Σ comb(E,j) × 28^(E−j)` for j from 0 through D, and the denominator is `29^E`, with E = 12,901 and D = 86. The script uses exact integers for that sum and 80-digit decimal arithmetic to render the ratio. It records hashes of both exact integers and supplies their reconstruction formulas. No normal approximation is used.

The separate checker reconstructs the same integer masses using a recurrence. It verifies the entire set of plotting bins against exact integer totals, independently recounts all 56 source files with regular expressions, and exhausts twelve small uniform-alphabet/page-length cases. Those controls include overlapping edges, multiple pages, empty pages and single-rune pages. They check the calculation and boundary handling; they do not authenticate the underlying handwriting.

## What remains possible

The model assigns this event a very small but nonzero probability. That is statistical evidence against the model, not a mathematical impossibility certificate. It neither selects an alternative model nor explains the suppression.

In particular, the [multiplicative running-sum model](#/wiki/doublets?section=ea-constraint) has a different equation. There, with nonzero keys modulo 29, a repeat can be determined by a particular plaintext rune. Uniform selection of its nonzero keys does not imply a repeat probability of 1/29. This experiment must not be used to reject that construction.

## Reproduce the comparison

Download this experiment's bundle and preserve its folders. Python 3 standard library only; no network, API, or model is required.

```text
python experiments/records/uniform-additive-doublets/run.py --check
python experiments/records/uniform-additive-doublets/check.py
python experiments/records/uniform-additive-doublets/plot.py --check
```

The first verifies the input hashes, per-page counts, exact tail and saved bins. The second uses the independent recurrence and controls. The third checks the chart against the saved probabilities. To regenerate, run the producer with `--write` and the plotter without `--check`.

The [committed plan](experiments/plans/uniform-additive-doublets.md) was fixed before these new calculations, after the prior count and claim were known. This is computationally checked replication; human review is pending. See [doublet definitions](#/wiki/doublets), [null-model selection](#/wiki/null-models), and [what a scoped exclusion means](#/wiki/first-experiment?section=exclusions).
