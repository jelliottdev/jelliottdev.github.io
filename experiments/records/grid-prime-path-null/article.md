# Are three missing grid primes unusual under fixed shuffles?

The [directional prime-path reconstruction](#/experiments/grid-prime-paths) finds 191 prime-path occurrences and 46 of 49 possible decimal-prime values in the first characters of LP2-49–51's grid. Three values are absent. This experiment asks a narrower statistical question: **if the same first digits were rearranged without changing their counts, how often would at least three values be absent under the identical path rule?**

![Histogram of missing prime values in two sets of 5,000 shuffled grids; the actual grid has three missing values.](experiments/records/grid-prime-path-null/missing-primes.svg)

The shaded column marks the observed count of three. It is not a fitted threshold or a third control.

## Fixed rule and controls

The [plan](experiments/records/grid-prime-path-null/plan.json) was saved with the two controls, four statistics, replicate count and seed before running them. Stack 32 rows of eight first digits in page order. Enumerate all 1,364 four-cell straight directed paths in eight directions, allowing page crossings. Reject paths containing a `4`. Read the four remaining digits as a decimal integer, including leading-zero strings, and test primality. There are 49 possible prime values from four positions over digits 0–3.

Each control repeats this entire fixed calculation 5,000 times:

1. **Global shuffle:** permute all 256 first digits; preserve their overall counts.
2. **Within-row shuffle:** shuffle the eight first digits independently in every manuscript row; preserve each row's composition and its page location.

Both destroy some spatial arrangement while retaining different amounts of local structure. Neither is a model of how the manuscript was actually made.

## Results

| Statistic | Observed grid | Global shuffle mean | Within-row mean |
| --- | ---: | ---: | ---: |
| Eligible paths | 1,058 | 1,034.54 | 1,043.22 |
| Prime-path occurrences | 191 | 189.62 | 191.42 |
| Distinct prime values present | 46 | 47.75 | 47.75 |
| Prime values absent | 3 | 1.25 | 1.25 |

At least three values were absent in **761 of 5,000** global shuffles and **763 of 5,000** within-row shuffles. The inclusive plus-one empirical upper-tail estimates are **15.24%** and **15.28%**. Three missing values are therefore not rare under either declared control. The complete [result file](experiments/records/grid-prime-path-null/results.json) retains the histogram and both empirical tails for every predeclared statistic, not just the favorable comparison.

This does **not** assign a chance probability to the particular names `1033`, `2213` and `3301`: those values were noticed before this test was designed. It does not account for trying other layouts, directions, path lengths, bases or visually selected patterns. It also does not test any decryption. The result weakens an argument from the *number* of missing values under these two nulls; it cannot rule out a construction based on a more specific independently predicted feature.

## Reproduce

Download the [experiment bundle](downloads/experiments/grid-prime-path-null.zip), extract it with its directory structure, then run Python 3.12 or later:

```text
python experiments/records/grid-prime-path-null/run.py --check
python experiments/records/grid-prime-path-null/check.py
python experiments/records/grid-prime-path-null/plot.py --check
```

The first script reruns all 10,000 control grids from seed `33012026` and checks the saved JSON byte for byte. The second independently enumerates endpoint pairs with a sieve for the observed grid and 24 fixed shuffled examples; it also checks the histogram arithmetic. The chart script checks the SVG against the saved histograms. The bundled [grid export](exports/alphanumeric-grids.json) supplies the 256 first digits, and the report pins its hash. Since the five documented archive-versus-wiki transcription differences affect only **second** characters, the numeric path statistic is unchanged by those five differences. Other unreviewed first-digit errors would require a new sensitivity test.
