## Question

Do the original-order rune-word lengths from the Warning, Welcome, first koan and second koan give unusually similar means in sixteen columns, compared with unrestricted permutations of those same lengths?

This record reproduces a supplied numerical observation. The arrangement and approximate result were already known. It tests one stated comparison, not whether the authors intentionally designed the text this way.

## Reconstruct the object before testing it

Use the archived ciphertext, in manuscript order. Count runes, not Latin letters: a rune labeled TH still has length one. Include headings and the interrupting F runes. Remove slash and newline wrapping, concatenate successive pages within each section, and retain other word boundaries. An internal apostrophe belongs to the same word and contributes no rune.

| Section | Pages | Words | Runes |
| --- | --- | --- | --- |
| Warning | LP1-01 | 45 | 184 |
| Welcome | LP1-03–04 | 124 | 515 |
| First koan | LP1-06–09 | 208 | 778 |
| Second koan | LP1-14–15 | 87 | 319 |
| Total | Nine pages | 464 | 1796 |

All 464 reconstructed lengths match the supplied vector exactly. Treating the apostrophe in DON'T as a word separator instead produces 465 tokens: two pieces of lengths three and one replace one four-rune word. That would shift all later column assignments.

The table is filled across each row from left to right, sixteen words at a time. There are 29 rows. Word 1 goes in row 1, column 1; word 16 in row 1, column 16; word 17 in row 2, column 1. Section boundaries do not reset the column counter.

The full [29-by-16 length table](experiments/records/lp1-word-length-balance/length-table.csv) is downloadable. The [word ledger](experiments/records/lp1-word-length-balance/words.json) gives each word's original ciphertext, rune length, section, contributing pages, row and column. A word crossing a page boundary records both pages. Neither file silently substitutes contextual English.

## Statistic and exact expectation

Let N = 464, k = 16 columns and m = 29 words per column. For column j, let S_j be its total rune count and M_j = S_j / m its mean word length. Let M be the overall mean word length, 1796/464.

Use the population variance across the sixteen column means:

```
V = sum((M_j - M)^2) / k
R = V / E[V under the declared shuffle model]
```

Each shuffle uniformly permutes the same list of 464 lengths. It keeps the overall distribution and total rune count but destroys word order, sentence structure and section membership. Duplicate lengths remain duplicate observations; there is no sampling of newly invented words.

For population variance sigma² of the fixed 464 lengths, the finite-population expectation is:

```
E[V] = sigma² × (k - 1) / (N - 1)
```

Why? Each column is a sample of m positions without replacement. Its mean has variance sigma² × (N-m)/(m(N-1)). The grand mean is fixed, so averaging the squared deviations of the column means has this same expectation; N = km gives the expression above. Independence between columns is not assumed.

The script uses exact rational arithmetic for this expectation and the observed ratio. For shuffle comparisons it uses an integer multiple of V, avoiding floating-point decisions at the tail boundary.

## Findings

The sixteen column totals are:

```
113, 105, 119, 111, 112, 118, 110, 111,
112, 112, 109, 101, 109, 126, 111, 117
```

Each total is divided by 29 to get its mean. Their deviations from the mean column total, 112.25, have squared sum 501.

| Quantity | Result |
| --- | --- |
| Observed variance of column means | 501/13456 |
| Exact shuffle expectation | 922305/6230128 |
| R | 77321/307435 = 0.25150356986029565 |
| Shuffles | 49,999 |
| Seed | 330146 |
| Shuffles with variance no greater than observed | 54 |
| Corrected lower-tail Monte Carlo estimate | (54 + 1)/(49,999 + 1) = 0.0011 |

The observed variance is about 25.15% of this model's expectation. It falls in the lower tail of the specified comparison, below the predeclared 0.05 threshold. The ratio and expectation are exact; the tail probability is estimated by simulation. Its Monte Carlo standard error is roughly 0.00015, not zero.

The [results file](experiments/records/lp1-word-length-balance/results.json) includes every simulated integer score, not only the tail count. The chart shows the observed column means. It does not plot the null distribution.

## What this does and does not establish

The counts, ordering and stated ratio reproduce from the archived runes. Under unrestricted permutations of this fixed multiset, arrangements at least this flat were uncommon in our run.

This is not a test against ordinary English. Unrestricted shuffling discards linguistic and section structure; an unusual result under that model need not be unusual among coherent texts. It is also not the probability that the observation is a coincidence, that the text was deliberately constructed, or that this arrangement is useful for decryption.

The original observation resulted from exploration. We knew the selected four sections, width and approximate ratio before this run. The plan was committed before this simulation, but that does not make the original discovery prospective. The reported tail estimate does not account for all earlier choices of populations, widths, orders and statistics.

The supplied Alice, Gateless Gate and other-LP window counts have not been reproduced here. Exact corpora and conversion rules would be needed. Overlapping windows are dependent, so a fraction of matching windows is not automatically an independent-trial significance calculation.

Keeping punctuation and word boundaries fixed while applying one-output-rune-per-input-rune substitutions preserves these lengths. Decoding does not provide independent confirmation of the same length pattern. Read [cipher invariants](#/wiki/cipher-invariants) and [search space and bounds](#/wiki/search-space) before extending the claim.

## Reproduce and inspect

Extract this experiment's ZIP with its directory structure intact. Python 3 is sufficient; there are no third-party dependencies or network calls.

```
python experiments/records/lp1-word-length-balance/run.py --check
python experiments/records/lp1-word-length-balance/check.py
```

The first command repeats all 49,999 shuffles and compares the complete results and word ledger. The independent checker uses a character scanner rather than the runner's regular expression, compares every token and length, calculates the observed variance directly from rational column means, and validates the null expectation by exhaustively enumerating two four-element teaching populations. It also independently calculates the first 32 null scores and audits the full saved tail count. A full rerun agreed.

To regenerate the CSV and chart from the saved outputs:

```
python experiments/records/lp1-word-length-balance/plot.py
```

Computational review is complete; human review is pending. The scripts and fixed input hashes define this result. The supplied vector is included only as a comparison target, not used to generate the measured lengths.

## Related questions remain separate

Three related comparisons are complete: [section-preserving shuffles](#/experiments/lp1-section-balance), [all 24 section orders](#/experiments/lp1-section-order), and [six declared widths](#/experiments/lp1-width-selection). They test different choices in the same selected word object and are not independent confirmations. Preserving sentence structure remains a separate comparison requiring an explicit protocol.

Section-contribution ledgers, sentence-removal scans, unchanged-rune grilles and the proposed 928-word carrier answer different questions. They are not findings of this record. In particular, 464 is a word count and 1,796 is a rune count; subtracting a count of unchanged runes from 464 would mix units.

## Sources and selection history

Inputs are the nine archived LP1 transcription files, with SHA-256 hashes in the plan and record. The complete supplied numerical vector is preserved in submitted-lengths.json. No missing screenshots, spreadsheets or named attachments were treated as available data. The initial count and exact-R reconstruction preceded the frozen simulation plan; that exploratory step is disclosed rather than described as a blind test.
