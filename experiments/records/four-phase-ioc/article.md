## Finding

**Splitting the unsolved rune stream into four alternating streams does not expose the concentration expected from four simple substitution alphabets.** The four measured collision rates lie within the middle 95% of page-preserving shuffled comparisons. A planted four-stream example is detected by the same measure. This says nothing decisive about four separate running keys, feedback ciphers or a different way to assign runes to streams.

![Successive rune positions assigned to four phases, followed by each phase's observed collision rate and the shuffled reference interval.](experiments/records/four-phase-ioc/phase-comparison.svg)

Take every fourth rune, starting with positions zero, one, two and three. For each resulting stream, the index of coincidence (IoC) is the chance that two different positions contain the same rune. A fixed substitution or a fixed additive shift changes rune labels but preserves that concentration. An independent keyed stream that continually changes its substitution need not preserve it. [How IoC works](#/wiki/index-of-coincidence).

| Check | Manuscript | Page-shuffle comparison |
| --- | ---: | ---: |
| Mean IoC across four phases | 0.034511 | 0.034416–0.034551 middle 95%; 361 of 1,999 shuffles at least as high |
| Highest phase IoC | 0.034564 | 0.034460–0.034697 middle 95%; 945 of 1,999 shuffles at least as high |

The two upper-tail estimates are **0.181** and **0.473**. Neither is unusual; correcting for checking both measures gives a smallest adjusted estimate of **0.362**. Each comparison shuffles rune order *within each page*, keeping its length and rune counts. It then repeats the four-way split from the start of the concatenated book. Thus the test asks whether the original order adds a four-phase concentration signal beyond the fixed page histograms.

## What was actually tested

The source is the [published “literal imperatives” sweep](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/C-literal-imperatives/RESULTS.md), which includes decimation and four-way interleaving among 185 operations. **This is an independent, narrower test, not a replay of its decoder verdict.** Its public checkout omits the generated nine-register language model and at least one corpus needed to rebuild it, so a fresh clone cannot currently rerun that entire scorer. The present record uses only the archived runes and a fully specified statistical comparison.

The source's phrase “LP2 pages 0–54” hides a numbering detail. Its loader drops an all-number page before numbering rune-bearing segments. Its 12,956-rune stream matches the actual images **LP2-00 through LP2-55, excluding number-only LP2-50**. We use those actual page labels: 55 rune-bearing pages, with the phase count continuing across page breaks. [Manuscript reader](#/reader).

As a power check, we Atbash-decoded the 184-rune [LP1 warning page](#/reader/lp1-01), made four copies shifted by 0, 3, 7 and 11 rune places, and interleaved them. Their mean phase IoC was **0.0640**. None of 1,999 whole-stream shuffles reached it. This confirms that the measure can see a strong four-stream substitution signal; it is not a control for every plausible cipher.

## Repeat the check

Download [this experiment](downloads/experiments/four-phase-ioc.zip) for the script, fixed plan, input text, results and figure. From the repository root run:

```text
python experiments/records/four-phase-ioc/run.py --check
python experiments/records/four-phase-ioc/check.py
```

The [plan](experiments/records/four-phase-ioc/plan.json) fixes the page mapping, two measures, shuffling rule and 1,999 trials. The [results](experiments/records/four-phase-ioc/results.json) retain the observed scores and tail counts. An [independent arithmetic check](experiments/records/four-phase-ioc/check.json) repeats the mean-IoC comparison with another random seed. The result is conditional on this particular four-phase concentration model; it does not close the broader hint or the source's other operations.
