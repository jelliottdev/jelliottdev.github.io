# LP2-31: periodic IoC for periods 2–20

**Computationally checked; human review pending.** Codex reran the script and reviewed the separate position-pair oracle on 20 October 2026. This is a bounded statistical result, not a decipherment or a human-reviewed conclusion.

## Question

Does LP2-31 have an unusually large within-column coincidence score at any period from 2 through 20, relative to random reorderings of the same rune multiset?

This is a test of one ordering statistic. It does not attempt decryption or determine whether the page uses Vigenère.

## Scope fixed before the first run

The plan is in `plan.json`, committed as `e515465` before computing the first result. It selects LP2-31, periods 2–20 inclusive, offset zero, 999 shuffles, seed 330131 and a 0.05 threshold. These are declared choices for this run, not a claim that the question or page was selected independently of all prior research.

The input is the complete archived rune stream, including headings. Remove every character outside the 29-rune alphabet before assigning positions. No corrections, decryption, region selection or cross-page concatenation are applied. The resulting length is 269 runes. Input paths and SHA-256 hashes are in `record.json` and `results.json`.

## Method

For period k, put positions with the same remainder modulo k in the same column. Count matching ordered pairs in each column and add them. Divide by the total number of ordered pairs available within all columns:

```
pooled IoC(k) = sum over columns and symbols of n(c,s)*(n(c,s)-1)
                / sum over columns of N(c)*(N(c)-1)
```

This weights columns by their number of pairs; it is not the unweighted mean of column IoCs. No pairs between different columns count.

Take the maximum over all 19 periods. Shuffle the original rune list afresh for each trial, preserving its exact symbol counts. Repeat the entire 19-period scan on every shuffled version and retain that trial's maximum. Compare maxima to maxima, rather than comparing the selected observed peak with an unselected single-period null distribution.

The random generator is Python's `random.Random(330131)`, using `shuffle`. Exact rational comparisons include ties. The Monte Carlo value is:

```
(1 + number of shuffled maxima >= observed maximum) / (999 + 1)
```

All observed period scores are retained. Each shuffled trial stores all 19 numerators, aligned with the observed periods. Their denominators do not depend on rune order and are stored once in the observed rows. The trial maximum is also stored as an exact fraction.

## Reproduce

From the repository root, using Python 3.12.10 and its standard library:

```
python experiments/records/lp2-31-periodic-ioc/check.py
python experiments/records/lp2-31-periodic-ioc/run.py --check
```

The independent check enumerates pairs of positions directly, instead of counting frequencies in columns. It checks a constant string, an alternating string, and every tested period of the actual page. The alternating control has pooled IoC 1 at period 2.

The full rerun compares every stored field, including all shuffle scores and input hashes. It should report exact reproduction and:

```
n: 269
best_periods: [13]
exceedances: 213
monte_carlo_p: 0.214
below_threshold: false
```

To save a separate report:

```
python experiments/records/lp2-31-periodic-ioc/run.py --output my-periodic-ioc.json
```

An existing output file is never overwritten. No network service, model, API key or third-party package is used. A changed input hash or random-generator behavior can prevent byte-for-byte reproduction; investigate rather than replacing the expected output automatically.

## Results

![Observed pooled IoC by period. The highest bar is period 13; the maximum-adjusted shuffle comparison is p = 0.214.](experiments/records/lp2-31-periodic-ioc/period-scan.svg)


Period 13 has the unique largest observed score: 216 / 5300 = 0.04075471698. Its columns contain 20 or 21 runes.

Of 999 random reorderings, 213 have a maximum at least this large somewhere in the same period range. The corrected Monte Carlo value is 214 / 1000 = 0.214. It is not below the declared 0.05 threshold.

For scale, the approximate Monte Carlo standard error of the estimated tail frequency is 0.013, using sqrt(q*(1-q)/999) with q = 213/999. This describes simulation uncertainty, not uncertainty about a cipher or plaintext. The reported Monte Carlo value has increments of 0.001.

## Interpretation and limitations

This run does not provide evidence, at the declared threshold, for singling out period 13 from this scan. It does not establish that LP2-31 lacks periodic structure. A cipher may produce structure that this statistic, input convention or period range does not detect.

The null model treats rune order as exchangeable conditional on its counts. It does not preserve word lengths, punctuation positions, local repeated patterns or possible region boundaries. Rejecting it would not prove any particular encryption method. Failing to reject it does not prove randomness.

The maximum comparison accounts for selecting among periods 2–20 in this run. It does not correct for choosing LP2-31, trying different text regions or previous unrelated tests. Periods outside the range, other pages, corrected streams, alternative statistics and actual key searches remain untested here.

No shift or Vigenère key is inferred. The period-13 peak is retained as a descriptive result, not promoted to a solution.

## Sources and related work

- [LP2-31 record and original-source links](https://jelliottdev.github.io/#/page/lp2-31)
- [IoC definition, baseline and invariants](https://jelliottdev.github.io/#/wiki/index-of-coincidence)
- [Reproducibility requirements](https://jelliottdev.github.io/#/wiki/reproducibility)

The whole-page baseline does not test ordering: shuffling preserves global IoC. This experiment adds an order-sensitive column statistic and a declared shuffle comparison. No earlier experiment is imported as a completed run.

## Retest and changes after inspection

On 20 October 2026, the independent position-pair check passed, and all observed and simulated numerical fields reproduced exactly. The only difference from the first saved output was the SHA-256 of `data/index.json`, whose page metadata had since changed. The plan and rune input hashes were unchanged. No period range, threshold, seed, sample count, or scoring rule was changed.

The original report is preserved as [original output](experiments/records/lp2-31-periodic-ioc/results-original.json). The [current report](experiments/records/lp2-31-periodic-ioc/results.json) records the current input hash. The checked script reproduces the current report exactly, including all 999 trials. The [chart script](experiments/records/lp2-31-periodic-ioc/plot.py) reads that report without running another experiment.

This record is the baseline for the periodic-IoC shuffle family. Future variants must identify each changed scope field and give their own plan, output and interpretation. There are no completed variants yet. Human review is still pending; the computational review was performed by Codex, not by an independent human researcher.
