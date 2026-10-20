# Are three-rune repeats unusually frequent?

Finding a repeated group of runes is easy to notice. Deciding whether there are more repeats than the page's symbol frequencies would ordinarily produce is a different question. This experiment compares a fixed repeat count across LP2-00–55 with whole-page shuffles that preserve every page's rune frequencies.

The archived input contains **55 matching pairs of three-rune windows**. Of 999 shuffled datasets, 798 have at least 55. The corrected upper-tail p-value is **0.799**, above the predeclared 0.05 threshold. This test provides no evidence of excess trigram repetition under this particular model.

## Count pairs, not just patterns

A trigram is a window of three consecutive runes. Move the window one rune at a time, including overlaps. A stream of N runes supplies `max(0, N − 2)` windows.

If one trigram occurs c times on a page, it contributes `c × (c − 1) / 2` matching pairs. The statistic adds these contributions over patterns and then over pages. It never compares a window on one page with a window on another.

| Invented stream | Three-rune windows | Matching pairs |
| --- | --- | --- |
| ABC | ABC | 0 |
| AAAA | AAA, AAA | 1 |
| AAAAA | AAA, AAA, AAA | 3 |
| ABABA | ABA, BAB, ABA | 1 |

For AAAAA, the three starting positions are 0, 1 and 2. The matching pairs are (0,1), (0,2) and (1,2). Counting “one repeated pattern” would measure something different. These letters are illustrative single symbols, not manuscript plaintext.

## Input and boundaries

The input retains all recognized alphabet runes from the archived transcriptions, including headings. Punctuation, word separators, line markers and other non-rune characters are removed. Windows can therefore cross an archived word or line boundary. They do not wrap around the end of a page.

LP2-50 has no recognized runes. It remains in the report with zero windows and zero matching pairs. Across the other 55 pages there are 12,846 windows. The input hashes and full alphabet source are recorded in the plan.

This test concerns the archived rune stream. It is not a fresh visual transcription, a count of repeated words, or a comparison of decoded English. See the [n-gram guide](#/wiki/rune-ngrams) for source-position conventions and examples of repeats that cross separators.

## What the shuffles preserve

Each simulated dataset independently rearranges the full rune stream of every page. It preserves each page's length and every single-rune count. Runes never move between pages. The procedure then calculates the same overlapping-window statistic on the shuffled pages and adds their scores.

This changes adjacency. It does not preserve row composition, word lengths as linguistic units, existing bigrams or repeated phrases. A different comparison model could answer a different question.

The calculation does not assume the overlapping windows are independent observations. It simulates whole streams and applies the full counting rule, including overlaps, to each simulated stream.

## Recorded result

![Distribution of matching trigram-pair totals across 999 shuffled LP2 datasets, compared with the observed total of 55.](experiments/records/lp2-trigram-repeats/null-distribution.svg)

| Quantity | Result |
| --- | --- |
| Observed matching pairs | 55 |
| Distinct repeated patterns, counted within page | 55 |
| Shuffled datasets | 999 |
| Shuffled total range | 33–89 |
| Mean shuffled total | Approximately 61.39 |
| Shuffled totals at least 55 | 798 |
| Corrected upper-tail p-value | (798 + 1) / (999 + 1) = 0.799 |
| Declared threshold | 0.05 |

In this observed dataset, each repeated pattern occurs exactly twice within its page, so the pattern count and pair count happen to agree. The controls above show why those counts need not agree generally.

The upper tail includes ties. The numerator and denominator each receive a one-count correction for the sampled permutation calculation, as described in the [SciPy permutation-test documentation](https://docs.scipy.org/doc/scipy-1.16.0/reference/generated/scipy.stats.permutation_test.html). The runner uses its own standard-library shuffles and integer score, not SciPy's implementation.

The simulation is an estimate, not an enumeration of every possible arrangement. Its approximate Monte Carlo standard error is 0.013, using `sqrt(q × (1 − q) / 999)` with `q = 798 / 999`. That sampling uncertainty does not account for transcription uncertainty or a poorly chosen model.

The observed total is below the simulation mean, but the declared question concerns an **excess**. This record does not reinterpret the result as a significant deficit or switch to a lower-tail test after inspection.

## Reproduce and inspect

From the repository root, using Python 3.12.10 and its standard library:

```sh
python experiments/records/lp2-trigram-repeats/run.py --check
python experiments/records/lp2-trigram-repeats/check.py
```

The first command repeats all observed counts and 999 complete-dataset shuffles with seed 330134, comparing every field against the saved report. Random-number implementation details are part of reproducibility; use the recorded Python environment when comparing exact simulated sequences.

The separate checker compares window pairs directly instead of using the runner's frequency formula. It checks every observed page and the first three simulated datasets, then audits all 999 saved score vectors, totals, tie decisions and the corrected tail calculation. It also verifies the complete observed pattern list and every starting position. A full second run separately verifies the remaining simulated values.

[Download per-page counts as CSV](experiments/records/lp2-trigram-repeats/observed-pages.csv), including the zero-rune page. [Download the full JSON report](experiments/records/lp2-trigram-repeats/results.json) for every repeated pattern, its rune indices and zero-based starting positions, plus all simulated page-score vectors. These vectors follow `null_page_order`; they are retained for auditing, not presented as separate page-level significance tests.

To save another run without replacing the reviewed result:

```sh
python experiments/records/lp2-trigram-repeats/run.py --output trigram-rerun.json
```

The destination must not already exist. To regenerate the chart and CSV from the stored result:

```sh
python experiments/records/lp2-trigram-repeats/plot.py
```

These commands read local files and do not use an AI service.

## What was decided before running

The plan and runner were committed as `70b8095` before the full-dataset calculation. Window length three, all declared pages, the aggregate pair statistic, upper tail, shuffle model, seed, trial count and threshold were fixed in that plan. None changed after the result.

The existing descriptive guide already reported no repeated trigrams on LP2-31. Repetition was also a topic of interest before this experiment. The plan discloses that prior knowledge; this is not a blind investigation of previously unseen manuscript data.

Codex performed the full rerun and independent checks on 20 October 2026. Human review remains pending.

## Limits and related tests

A large p-value does not demonstrate randomness or exclude encryption. This result concerns the aggregate excess of within-page exact trigrams under one model. It does not establish the status of a particular repeated phrase, a selected page, another window length, approximate matches or repeats between pages.

Changing window length or preserving additional structure in the shuffles belongs in a planned family variant. If the next test selects the strongest result among several lengths or regions, that selection must also be repeated in its comparison procedure. The [null-model guide](#/wiki/null-models) explains why.

This measurement also cannot distinguish a fixed one-to-one alphabet substitution from its input: renaming symbols preserves equal-window relationships. Rearranging rune positions can change those relationships. See [cipher invariants](#/wiki/cipher-invariants) before using a repeat score to rank candidate transformations.
