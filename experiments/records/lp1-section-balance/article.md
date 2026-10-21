# Does preserving each section change the column-balance result?

The fixed 464-word arrangement remains unusually flat under a null that shuffles word lengths only within their original four sections. All original section slots and the continuous sixteen-column layout are preserved. This is a sensitivity variant of `lp1-word-length-balance`, not an independent discovery.

| Quantity | Unrestricted baseline | Within-section variant |
| --- | ---: | ---: |
| Observed integer score | 128256 | 128256 |
| Observed column-mean variance | 501/13456 | 501/13456 |
| Observed variance / model expectation | 0.25150357 | 0.25209625 |
| Null trials | 49,999 | 49,999 |
| Trials at or below observed, including ties | 54 | 88 |
| Plus-one lower-tail estimate | 0.0011 | 0.00178 |

The constrained expectation is calculated separately. Its exact expected integer score is `612019253902976/1202967183`, and expected column-mean variance is `4781400421117/32374252828896`. The unchanged observed variance divided by that expectation is `1205373117366/4781400421117`.

The four sections contain 45, 124, 208 and 87 words. Their boundaries do not reset the column position. The report preserves every section's slot counts in all sixteen columns, exact expected column sums and variances, and all 49,999 null scores. A singleton-section boundary and unequal section sizes are covered by small exhaustive controls.

## What changes between the two models?

The baseline permits any word length to move to any of the 464 slots. This variant permits a word length to move only to a slot in its original section. The lengths themselves, section order and observed arrangement remain unchanged. A section may occupy different numbers of slots in different columns, so keeping its slots matters as well as keeping its histogram.

The slot diagram shows those fixed memberships. Colors identify the four sections, not high or low word lengths. The same word may have several interchangeable positions within its color. A single section boundary can cut across a row; the next section continues at the next column.

The two histogram panels use identical integer-score bins, displayed on a common column-mean variance scale. The dashed line is the unchanged observed variance. Lower variance means more similar column means. Every one of the 49,999 null scores per model contributes to its panel; the complete bin counts are downloadable as CSV. The shared seed number does not pair individual trials because the procedures consume random choices differently.

## Why the expectation changes

Under unrestricted shuffling, every slot samples the same pool of lengths. Under within-section shuffling, each slot samples only its section's pool. The four pools have different means and variances. Columns also contain different section slot counts. Consequently, their expected sums need not be identical, even though every column still contains 29 words.

For section size N, population variance v and c slots in one column, its sum contributes variance `c*(N-c)*v/(N-1)`. Contributions from independently shuffled sections add. The expected squared distance from the fixed overall mean also includes the difference between each column's expected sum and the overall mean. The script uses exact fractions; the checker obtains the same expectation through pairwise position moments. The ratio in the table therefore uses each model's own expectation.

## Reproduce

Extract the experiment ZIP with folders intact, or use the repository. Python 3 standard library is sufficient. Run `python experiments/records/lp1-section-balance/run.py --check` to reproduce all constrained scores, run the independent checker and verify the figures. Use `--output section-replay` to retain new files in a new directory.

The individual stages can also be run from the root with new output paths:

```sh
python scripts/test_lp1_section_balance.py
python scripts/lp1_section_balance.py --output section-results.json
python scripts/check_lp1_section_balance.py section-results.json --receipt section-audit.json
```

The [protocol](experiments/plans/lp1-section-balance.md) was committed before constrained shuffles were generated. The producer uses the hashed word ledger and source dependencies. The checker independently scans the original archived text, verifies all 464 words, reconstructs every permutation with explicit index swaps, and calculates the expectation through position-pair second moments. It imports no producer code. Both implementations share Python's pseudorandom primitive.

## Interpretation and publication status

Both estimates are below the predeclared 0.05 threshold. Preserving section-level length distributions does not remove the low-variance result in this fixed test. The two tests share the same selected arrangement; their p-values must not be combined as independent evidence. The original exploration is not included in either null. Neither model preserves sentence syntax, and neither tests a grille, carrier text, authorial intent or a decryption.

Human review remains pending. Saved results and the independent receipt are preserved here without overwriting the original baseline. The figures and histogram CSV are generated from those saved reports; the baseline distribution is reused from its published record, not simulated as part of this variant.

## Related explanations

See [the unrestricted baseline](#/experiments/lp1-word-length-balance), [word-length conventions](#/wiki/word-lengths), and [null models and selection](#/wiki/null-models). Preserving section distributions is only one possible constraint; preserving sentences or testing alternative section orders would require a separately declared variant.
