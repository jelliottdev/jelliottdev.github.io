# Do the three 1,433-rune sections align?

**Result:** No distinctive printed-order arithmetic reading appears in this bounded test. The best of **12 fixed outputs** has an index of coincidence of **0.034813**. When the same 12-way choice is repeated after independent circular shifts, **465 of 999** trials score at least as high. The reported equal lengths are real; they do not, by themselves, choose an alignment or arithmetic operation.

![The observed best score nearly coincides with the median of selected shifted controls.](experiments/records/section-1433-pairing/comparison.svg)

The [section-count source](#/wiki/section-rune-counts) identifies three streams of 1,433 runes. We rebuilt each directly from the archived page text, using its explicit section breaks:

| Stream | Construction | F rune |
| --- | --- | --- |
| Koan 2 + Spirals | LP1-14–15, then LP2-03–07 | Omit all 31 |
| Cuneiform | Second piece of LP2-33 through first piece of LP2-39 | Omit all 35 |
| Wing and Tree | LP2-27–32 | Retain all 52 |

For each of the **three pairings**, the test adds or subtracts corresponding zero-based rune indices modulo 29, with the second stream either forward or reversed. It measures the equal-rune-pair rate over the complete output (index of coincidence, or IoC). This yields four operations per pairing, 12 outputs in all; the largest score is the test statistic.

| Printed-order pairing | Best of four IoC |
| --- | ---: |
| Koan 2 + Spirals / Cuneiform | **0.034813** |
| Koan 2 + Spirals / Wing and Tree | 0.034618 |
| Cuneiform / Wing and Tree | 0.034524 |

The observed winner is reverse-subtraction of Cuneiform against Koan 2 + Spirals. The median **best-of-12** control score is **0.034799**, nearly the same. Each control trial draws a nonzero circular shift independently for each pair and **repeats the entire 12-output choice**. The saved report includes the 12 printed-order scores and all 999 selected control scores; an independent script recounts them.

This comparison is deliberately narrow. Its controls condition on the three previously noticed equal-length streams, the F-removal decisions, this operation family and IoC as the success measure. **466/1,000** is the add-one tail fraction for this conditional setup, *not* the chance of discovering the equality or a probability that the manuscript has no related cipher. Other transformations or a specific plaintext prediction would require a separately fixed test.

## Reproduce

From the repository root, run `python experiments/records/section-1433-pairing/run.py --check`, then `python experiments/records/section-1433-pairing/check.py`. Both use the Python standard library. The [plan](experiments/records/section-1433-pairing/plan.json) declares all 12 candidates and the control rule; [results](experiments/records/section-1433-pairing/results.json) save the input hashes and scores. The related [1,894-rune pairing](#/experiments/section-1894-pairing) uses the same arithmetic family on a separate reported equality.
