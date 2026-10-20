# Emirp sums at archived row boundaries

This variant asks whether the archived rows of LP2-00–55 produce an excess of **emirp-valued sums**. It follows the [prime-row baseline](#/experiments/lp2-row-prime-sums), keeping its pages, row lengths, input values, shuffle sequence, trial count and upper-tail rule.

There are 41 qualifying rows among 594 eligible rows. Of 999 simulated datasets, 539 have at least 41. The corrected upper-tail p-value is **0.540**. This does not provide evidence of excess emirp row sums under the declared shuffle model.

## What changes from the baseline?

The baseline counts a row when its Gematria Primus sum is prime. This variant adds two requirements: reversing its base-ten decimal digits must produce a prime, and the reversed value must differ from the original.

| Sum | Decimal reversal | Qualifies? |
| --- | --- | --- |
| 13 | 31 | Yes: distinct primes |
| 23 | 32 | No: the reversal is composite |
| 101 | 101 | No: a prime palindrome is excluded |
| 107 | 701 | Yes: distinct primes |

These are arithmetic controls, not selected manuscript observations. Reversal acts on the decimal digits of the completed sum. It does not reverse rune order, complement digits, reverse a prime ordinal or use another numeral base. See [emirps and decimal reversal](#/wiki/emirps).

Each eligible row counts once when it qualifies. Two different rows with the same qualifying sum still count as two rows; the statistic is not a count of distinct numerical values.

## What stays fixed?

Every nonempty archived line containing recognized runes is an eligible row, including headings. Non-rune characters are removed before summing Gematria Primus prime values. LP2-50 contributes no runic rows. No correction, decryption or respelling is applied.

For each simulated dataset, the full rune multiset of each page is shuffled and then divided using that page's original row lengths. This preserves page frequencies and row lengths, but not each row's original frequencies or word structure.

The seed remains 330133, with the same page order, trial order and Python shuffle calls as the baseline. There are 999 complete-dataset trials. The decision compares the global observed count with simulated global counts, includes ties, uses the plus-one Monte Carlo correction, and retains the 0.05 threshold.

The baseline excludes emirps from its scope; this variant explicitly tests them. Its other exclusions remain visible in the scope comparison. The baseline finding has not been replaced or reinterpreted.

## Recorded result

![Emirp row-sum counts across the baseline’s 999 shuffled datasets, with the observed count of 41 marked.](experiments/records/lp2-row-emirp-sums/null-distribution.svg)

| Quantity | Result |
| --- | --- |
| Eligible rows | 594 |
| Observed prime-valued rows, as in the baseline | 76 |
| Observed emirp-valued rows | 41 |
| Simulated emirp-count range | 20–60 |
| Mean simulated emirp count | Approximately 41.40 |
| Simulated totals at least 41 | 539 of 999 |
| Corrected upper-tail p-value | (539 + 1) / (999 + 1) = 0.540 |

The 41 emirp rows are a subset of the 76 prime rows. The two experiments are related measurements on the same observed and simulated inputs, not independent evidence. Comparing their p-values does not establish that one property is more intentional or more useful for decryption.

This is a sampled comparison. Its approximate Monte Carlo standard error is 0.016, calculated as `sqrt(q × (1 − q) / 999)` with `q = 539 / 999`. That estimate describes simulation uncertainty, not uncertainty about the transcription or the choice of model.

## Inspect and reproduce

From the repository root with Python 3.12.10:

```sh
python experiments/records/lp2-row-emirp-sums/run.py --check
python experiments/records/lp2-row-emirp-sums/check.py
```

The first command repeats every observed row and all 999 trials. The second verifies observed primality by trial division and reverses digits arithmetically with division and remainders. This differs from the runner's sieve and string reversal. It also independently checks the first three shuffled datasets and audits all stored totals, tail decisions and baseline prime-count vectors.

[Download the row CSV](experiments/records/lp2-row-emirp-sums/observed-rows.csv) for all 594 eligible rows, including those that do not qualify. Each row includes the page, one-based archived line number, rune count, sum, decimal reversal and both classifications. LP2-50 has no eligible CSV rows; it remains explicit in the full report.

[Download the JSON report](experiments/records/lp2-row-emirp-sums/results.json) for the observed rows and all trial counts. Each trial retains `page_counts` for emirps and `prime_page_counts` for comparison with the baseline. Both vectors follow `null_page_order`.

Save a new result without replacing the reviewed file:

```sh
python experiments/records/lp2-row-emirp-sums/run.py --output emirp-rerun.json
```

The output file must not already exist. The standard-library scripts read local files; no AI service is involved. Regenerate the chart and CSV with:

```sh
python experiments/records/lp2-row-emirp-sums/plot.py
```

## Plan and verification

The plan and runner were committed as `1d901b4` before the full calculation. The prime baseline was already known, and emirps were an existing topic of interest. The plan discloses that this is a follow-up rather than a blind discovery. No property, input rule, seed, threshold or tail changed after inspection.

The checker verifies that the baseline's unchanged plan fields still agree. Every observed sum and prime classification matches the earlier record; all 999 per-page prime-count vectors also match. Emirp counts never exceed their corresponding prime counts. A complete second execution reproduces the full result.

Codex performed these computational checks on 20 October 2026. Human review remains pending.

## Limits

The test concerns a global excess at archived row boundaries. It does not test selected words, decoded sentences, other numeral bases, alternative boundaries, prime-index transformations or the meaning of a particular number. It does not assign page-specific significance.

A result above the threshold does not prove that no row was deliberately constructed, nor that the manuscript is random. It says that this aggregate emirp count is not unusually high under this specific comparison. Alternative statistics selected after seeing results need a new declared procedure and an appropriate treatment of selection; see [null models](#/wiki/null-models).
