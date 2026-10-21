# Width selection in the four-section 464-word object

Freeze before computing any new width scores or controls.

## Question and declared choices

Does the minimum normalized column imbalance over widths **2, 4, 8, 16, 32 and 64** fall unusually low under unrestricted permutations of the same 464 word lengths, when every control receives the same six-width search?

This power-of-two set follows the supplied discussion and includes 64 as well as the earlier powers. It is not a search over every width. The original width-16 result and the discussion's qualitative observations were known before this plan. This variant cannot correct all choices made during the original discovery.

Use the original baseline's exact four sections, order, headings, interruptions, internal apostrophes and wrap rules, as pinned in `experiments/records/lp1-word-length-balance/plan.json`. Reconstruct and compare all 464 archived words before measurement. Freeze the baseline plan, word inventory and submitted lengths by SHA-256 in the companion JSON plan. Do not remove words, reorder sections, rotate the starting point, pad rows or optimize boundaries.

For width k, word i (zero-based) belongs to column i mod k. Partial final rows remain partial. Let n=464, n_j be column sizes, S_j column sums, T the total and D=sum(x_i²)−T²/n. Define weighted imbalance Q_k=sum(S_j²/n_j)−T²/n. Its unrestricted-permutation expectation is (k−1)D/(n−1). Compare R_k=Q_k/E(Q_k). Weighting by n_j accounts explicitly for unequal column sizes. At width 16, R agrees with the existing equal-column statistic.

The selection statistic is min R_k over all six widths. Retain every tying width. Normalizing the mean does not make the distributions identical across widths; the smallest R is not a width-specific p-value. Calibration is therefore against the minimum from each complete shuffled search, not against a fixed-width distribution.

## Controls and reporting

- 49,999 unrestricted length permutations; Python standard-library Random with seed 330146. Each trial starts from the original vector, as in the existing baseline. No new seed selection.
- Compute all six width scores for every trial. Retain every integer score and the selected minimum, including ties. Use exact rational comparisons.
- Report the selected lower tail with ties and plus-one estimate `(tail+1)/50000` at the declared 0.05 threshold. Also report all six unadjusted fixed-width tails as descriptive diagnostics, explicitly not six independent tests or six adjusted results.
- Verify the width-16 observed R and 54/49,999 tail against the existing baseline. Failure stops publication and requires investigation, not parameter adjustment.
- Independently reconstruct the lengths, explicitly replay Fisher–Yates, and compute Q from direct column slices rather than the producer's nested-width aggregation. Check all 299,994 null width scores, selected minima, ties and tail counts.
- Publish the complete width table, a selection-null figure, source hashes, report, independent receipt and offline reproduction. Clearly separate observed arrangement, null model, search bounds and original-selection limitations.

## Scope

This is a selection-aware variant in the existing word-balance family. It does not test coherent-language arrangements, preserve sections in the null, search all widths, calibrate the original exploration, reconstruct a grille, establish intent, or identify an unsolved-page cipher.
