# Do ciphertext-feedback coefficients reveal a reading?

One proposed cipher makes each key value depend on earlier **ciphertext** runes. In the [published D-04 source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/campaign18_skip/ctfeedback_coeffs.py), the feedback adds up to three earlier rune values, each multiplied by a chosen coefficient modulo 29. We ran its default search unchanged and separately checked a planted example *inside* that search's seed range.

## Finding

![Two known-rule plants score above the source's reading bar. The best coefficients on LP2-00, LP2-05, and LP2-20 score well below it.](experiments/records/dukotah-ciphertext-feedback-coefficients/coefficient-feedback.svg)

The source checks **5,072 coefficient vectors**, two constant seed values, both addition directions and one starting offset on each of **three pages**: **60,864 full-page decodes**. Its known-rule gate passes. None of the page winners reaches its **−5.2** English-score signal bar:

| Page | Best score | Coefficients | Source prose |
| --- | ---: | --- | ---: |
| LP2-00 | −6.90 | 14, 3, 1 | −6.86 |
| LP2-05 | −6.93 | 12, 28, 28 | −6.91 |
| LP2-20 | −6.89 | 2, 27, 1 | −6.89 |

The [source summary](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/campaign18_skip/armada2/COVERAGE-MATRIX.md) prints slightly different maxima for two pages. The current pinned executable and its independently rescored winning coefficients produce the values above. We cannot establish which earlier code or run produced the prose numbers. The bounded conclusion is unchanged: **these tested configurations do not yield a supported English reading on these three pages**.

## A control inside the actual search

The source's original gate plants a rule with coefficient **7** and constant seed **5**. It recovers the planted text perfectly, but the default LP2 search uses only seeds **0 and 1**. We therefore planted the same coefficient separately under seeds 0 and 1, then checked the full one-tap search of **112 configurations** for each. In both cases, the true rule ranked **first**, recovered **100%** of the planted rune indices and scored **−4.13**; the unit-coefficient comparison scored below **−7.0**.

These plants verify that this coefficient search can recognize a known rule in its tested seed range. They **do not** validate key-skip recovery: advancing through a constant seed always returns the same value, so a skip is invisible in the ciphertext. The source's gate and our added plants mainly exercise the coefficient term and scoring.

## Scope

The one-tap search uses all 28 nonzero multipliers. The two-tap search uses 840 nonzero pairs. The three-tap search uses 4,204 vectors, with the third tap restricted to **0, 1, 28, 2 or 27**. Every combination uses a source-defined English-scored beam of width 250 with at most three skips. The pages are **LP2-00, LP2-05 and LP2-20**, with 262–269 runes each; the other nonempty LP2 pages, other seeds, offsets, feedback functions and languages were not searched. The source driver prints a gate result but does not stop if the gate returns false; our captured run explicitly printed **PASS**.

The result does not exclude ciphertext feedback as a whole. Nor does a score below a historical bar establish that a proposed model is impossible. A further model would need its own specified rule, a matched positive control and a held-out reading test.

## Reproduce

The [source-read plan](experiments/records/dukotah-ciphertext-feedback-coefficients/plan.json) pins the revision, exact input hashes, coefficients and target pages before our run; it is not an independent preregistration of the published method. The [added-control plan](experiments/records/dukotah-ciphertext-feedback-coefficients/diagnostic-plan.json) was frozen before its two plant results. With the [pinned source checkout](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1) as `SOURCE`:

```text
python experiments/records/dukotah-ciphertext-feedback-coefficients/run.py --source-root SOURCE
python experiments/records/dukotah-ciphertext-feedback-coefficients/diagnostic.py --source-root SOURCE --check
python experiments/records/dukotah-ciphertext-feedback-coefficients/check.py --source-root SOURCE --check
python experiments/records/dukotah-ciphertext-feedback-coefficients/plot.py --check
```

The [complete source printout](experiments/records/dukotah-ciphertext-feedback-coefficients/source-replay-stdout.txt), [planted-control rows](experiments/records/dukotah-ciphertext-feedback-coefficients/diagnostic-results.json), and [checked summary](experiments/records/dukotah-ciphertext-feedback-coefficients/results.json) are retained. The checker independently constructs each winning feedback sequence before rescoring it with the pinned decoder.
