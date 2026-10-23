# Do the proposed section sizes form numerical matrices?

**Several proposed areas are exact counts of the archived transcription.** They use different representations: whole runes, decimal digits of Gematria Primus primes, or decimal digits of rune positions. This establishes how those areas were obtained. It does not supply an order for filling or reading a grid, much less decoded text.

| Pages | What is counted | Observed | Proposed arrangement |
| --- | --- | ---: | --- |
| LP2-00–02 | runes | 729 | 27 × 27 |
| LP2-03–07 | GP-prime digits | 2,345 | 35 × 67 |
| LP2-08–14 | runes | 1,729 | 7 × 13 × 19 |
| LP2-15 body | GP-prime digits | 289 | 17 × 17 |
| LP2-16–22 | GP-prime digits | 3,481 | 59 × 59 |
| LP2-27–31 | runes / zero-based index digits | 1,312 / 2,200 | 32 × 41 / 44 × 50 |
| LP2-32 | runes / zero-based index digits | 121 / 196 | 11 × 11 / 14 × 14 |
| LP2-33–39 | runes | 1,680 | 40 × 42 or 7 × 15 × 16 |

For LP2-15, *body* means the rune text after the first nine-rune header line. The complete page has 307 prime digits, so removing that specific header is essential to the 17 × 17 result. The 27 × 27 arrangement has a separate [route replay](#/experiments/totient-map-route), while the 17 × 17 and 59 × 59 streams have a separate [spiral and selector replay](#/experiments/cc-roman-matrix-replay). Those tests are not counted as new decryptions here.

Two other proposals require extra selections. LP2-08–14 gives **2,915** digits with one-based indices; 54 × 54 needs **2,916**. Adding the printed `7` seen on LP2-10 would fill one position, but that digit is not part of the rune stream and its placement is unspecified. LP2-23–26 contains **1,021** runes; 15 × 67 needs **1,005**. Removing 16 runes makes the arithmetic work, but this text-only test cannot identify which runes are red or authorize their exclusion. LP2-33–38 alone has 1,440 runes (36 × 40); LP2-39 has 240 (15 × 16). These component counts are in the [full results](experiments/records/cc-section-representation-census/results.json).

## How much does a square count narrow the choice?

![Among 820 contiguous LP2 page intervals, square lengths occur under every tested representation; the figure shows exact counts, not probabilities.](experiments/records/cc-section-representation-census/squares.svg)

We also counted **every 820 nonempty contiguous page ranges from LP2-00 through LP2-39** under all four representations. Eleven intervals have a square number of runes, eight a square number of prime digits, three a square number of zero-based index digits, and four a square number of one-based index digits. The proposed 27 × 27 rune interval, 59 × 59 prime-digit interval, and both LP2-32 squares are among them. The LP2-15 body is a different selection, because it starts *inside* a page.

Each full-page target length checked for recurrence occurs once among the 820 intervals *in that particular representation*. The partial-page LP2-15 body is outside this census. This is descriptive, not a uniqueness argument for the method: the targets and section breaks were observed first, intervals overlap, and rectangular lengths have many factor pairs. A compelling cipher proposal would specify the representation, page boundary, any omitted runes, dimensions, start cell and traversal **before** asking whether its reading works on another section.

## Counting rule and scope

We kept only the 29 Gematria Primus runes in the archived LP2-00–39 text files. Headings count unless an exception is stated; spaces, separators, punctuation and printed non-rune digits do not. For digit representations, each rune's unpadded decimal value contributes its own number of digits. For example, a prime value of `109` contributes three cells. The group counts reuse the already pinned [source audit](research/source-intake/cc-matrix-counts.json); the new comparison enumerates every contiguous interval. The checker independently reads the per-page JSON raw transcription, verifies its rune stream against the text file, and recomputes the interval and square counts.

This is one archived transcription, not an independent visual adjudication of disputed runes or ink colors. The proposed grouping, representations and matrix shapes were exploratory. The interval census does not correct for searching other boundaries, rearrangements, partial-page cuts or representations and supplies no chance probability.

To reproduce from the repository root, run `python experiments/records/cc-section-representation-census/run.py --check` and `python experiments/records/cc-section-representation-census/check.py`. The [plan](experiments/records/cc-section-representation-census/plan.json), [results](experiments/records/cc-section-representation-census/results.json) and [independent checker](experiments/records/cc-section-representation-census/check.py) give the exact rules and files.
