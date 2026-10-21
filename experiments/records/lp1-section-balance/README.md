# LP1 section-preserving column balance: checked research record

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

## Reproduce

Python 3 standard library, from the repository root, with new output paths:

```sh
python scripts/test_lp1_section_balance.py
python scripts/lp1_section_balance.py --output section-results.json
python scripts/check_lp1_section_balance.py section-results.json --receipt section-audit.json
```

The [protocol](../../plans/lp1-section-balance.md) was committed before constrained shuffles were generated. The producer uses the hashed word ledger and source dependencies. The checker independently scans the original archived text, verifies all 464 words, reconstructs every permutation with explicit index swaps, and calculates the expectation through position-pair second moments. It imports no producer code. Both implementations share Python's pseudorandom primitive.

## Interpretation and publication status

Both estimates are below the predeclared 0.05 threshold. Preserving section-level length distributions does not remove the low-variance result in this fixed test. The two tests share the same selected arrangement; their p-values must not be combined as independent evidence. The original exploration is not included in either null. Neither model preserves sentence syntax, and neither tests a grille, carrier text, authorial intent or a decryption.

The public family variant, comparative figures and bundled entry point are still being prepared. Human review remains pending. Saved results and the independent receipt are preserved here without overwriting the original baseline.
