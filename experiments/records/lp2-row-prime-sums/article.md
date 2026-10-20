# Prime-valued archived row sums

## Question and motivation

Gematria Primus assigns a prime value to each rune. Adding the values in a row can itself produce a prime. The presence of some such sums is not enough to show that the boundaries were designed to produce them.

This test asks whether the archived row boundaries across LP2-00–55 produce an unusually large total number of prime sums compared with shuffled text. It uses one combined statistic, rather than selecting promising pages or rows after inspection.

## Plan and eligible input

The plan and initial runner were committed as `f1779dc` before execution. Each archived transcription line containing at least one recognized rune defines a row. Include headings, remove non-alphabet characters, and apply no correction or decryption. Rows with no recognized runes do not receive a Gematria Primus sum.

The first invocation stopped before computing a result because LP2-50 has no runic rows. Commit `ec18a8f` removed an unnecessary requirement that every page contribute a row. The input rule itself did not change: rows without recognized runes were already excluded. LP2-50 remains in every dataset with a zero eligible-row count; its alphanumeric grid is not interpreted as runes. This implementation correction occurred before the first completed statistical result.

The final input has 594 eligible rows across 55 rune-bearing pages, with LP2-50 retained as the zero-row page in the declared 56-page scope.

## Statistic and comparison model

For each row, sum the Gematria Primus values of its runes. Count how many sums are prime, then add those counts across all selected pages. That combined count is the single test statistic.

For each simulated dataset, independently shuffle the full rune stream within each page. Partition the shuffled stream using that page's original row lengths. This preserves page-level rune counts and every row length, but does not preserve words, local ordering or each row's original composition.

Repeat for 999 datasets using Python's `random.Random(330133)`. Count null totals greater than or equal to the observed total, including ties. Use the plus-one Monte Carlo correction:

```
p = (1 + shuffled totals at least observed) / (1 + 999)
```

The declared test is one-sided: an excess of prime-valued row sums. It is not a test for a deficit, nor a two-sided test for any deviation. The threshold is 0.05. Per-page counts are retained for inspection but are not separate significance tests.

## Result

| Quantity | Observed or simulated value |
| --- | --- |
| Eligible rows | 594 |
| Observed prime-valued sums | 76 |
| Shuffled total range | 60–115 |
| Mean shuffled total | 83.786 |
| Shuffled totals at least 76 | 843 of 999 |
| Corrected one-sided p | 0.844 |
| Below the declared 0.05 threshold | No |

The observed count does not provide evidence of an excess under this model. The relatively high p-value does not establish randomness, disprove deliberate numerical design, or make the null model true.

The approximate Monte Carlo standard error is 0.0115, computed from the simulated tail frequency 843/999. This is simulation uncertainty, not a probability that a proposed encoding exists.

## Files and how to reproduce

Use Python 3.12.10; all scripts use the standard library.

```
python experiments/records/lp2-row-prime-sums/run.py --check
python experiments/records/lp2-row-prime-sums/check.py
```

The first command reruns every observed row calculation and all 999 full-dataset shuffles, then compares every saved field. The separate checker uses trial division instead of the runner's sieve for all observed sums and the first three simulated datasets. It also audits the totals, tail decisions and correction across all saved trials.

[Download all observed row sums as CSV](experiments/records/lp2-row-prime-sums/observed-rows.csv). The archived line number is one-based and includes the source file's line numbering. A zero-row page has no CSV row; it remains explicit in the JSON's page list.

[Download the complete report](experiments/records/lp2-row-prime-sums/results.json). It retains every observed row and all 999 per-page null-count vectors, aligned with `null_page_order`. The histogram and CSV are generated from this saved report:

```
python experiments/records/lp2-row-prime-sums/plot.py
```

To save a fresh result separately, run the main script with `--output my-row-primes.json`. It refuses to overwrite an existing result. No network connection or AI service is used.

## Retest and review

Codex repeated the full run and performed the independent checks on 20 October 2026. All observed sums and simulated records reproduced exactly. Apart from the pre-result zero-row handling correction described above, no statistic, input rule, seed, threshold, tail or null model changed. Human review remains pending.

## Limits and next variants

This analysis uses archived transcription boundaries, not a new visual verification of every printed row. Transcription errors, heading treatment or a different boundary convention could change the calculation.

It does not test emirps, reversals of decimal sums, prime ordinals, decoded readings, selected words, arbitrary regions, or the possibility that a few specific rows were deliberately chosen. It also does not correct for historical investigations or future choices among alternative statistics. The pages and statistic were selected because prime sums were already a topic of interest; this is not a blind discovery.

A different boundary rule or numerical property belongs in a separately planned variant. Keep the original result available rather than enlarging the search until an attractive pattern appears.

See [prime sums](#/wiki/prime-sums), [null models](#/wiki/null-models), and [documenting a reproducible attempt](#/wiki/reproducibility).
