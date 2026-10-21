# LP1 column balance after searching section orders

This variant belongs to the LP1 word-length and column-balance family. Human review remains pending.

## What was tested

The original 464-word sequence fills a table of 29 rows and 16 columns. Its column totals are unusually similar under the previously declared shuffle controls. This variant asks whether that comparison changes when a solver may rearrange the four intact sections and keep whichever arrangement has the most similar column totals.

The sections are Warning (45 words), Welcome (124), first koan (208), and second koan (87). Word order within each observed section remains unchanged. Every arrangement fills the table continuously, without resetting at section boundaries. The score is `Q = sum((16 * column_total - 1796)^2)`; lower scores mean more balanced columns.

The [protocol](experiments/plans/lp1-section-order.md) was committed before calculating the order search. It disclosed the already-known fixed-order results. Each of 49,999 controls shuffles lengths within the original sections, searches the same 24 orders, and retains its minimum. It would be unfair to search the observed data but compare that selected result with controls given only one arrangement.

## Results

No alternative order improves the original score, **128256**. Four orders tie for that minimum because they are cyclic rotations of the original arrangement.

| Representative order | Score Q |
| --- | ---: |
| Warning → Welcome → first koan → second koan | 128256 |
| Warning → Welcome → second koan → first koan | 295680 |
| Warning → first koan → Welcome → second koan | 257280 |
| Warning → first koan → second koan → Welcome | 407296 |
| Warning → second koan → Welcome → first koan | 215808 |
| Warning → second koan → first koan → Welcome | 337664 |

Each row represents four cyclic rotations with exactly the same score. Rotating the 464-word sequence shifts its sixteen column totals without changing their balance, since 464 is divisible by 16. Thus the 24 arrangements form six classes; this does **not** make the six scores independent.

**440 of 49,999 controls** have a selected minimum no greater than the observed minimum, ties included. The plus-one estimate is `(440 + 1) / 50000 = 0.00882`. The fixed-order within-section comparison was `0.00178`. The larger estimate reflects the extra opportunities given to every control, even though the observed minimum did not improve.

The result remains below the protocol's 0.05 threshold. It describes this precise word sequence, table width, score, shuffle model and section-order search. It does not estimate the probability of intentional design, provide a decryption, or correct for the wider exploration that originally selected the 464-word object and sixteen-column layout. The two estimates use the same shuffled sections and are not independent evidence.

## Verification and reproduction

The independent checker reconstructs the source tokens, generates permutations through explicit index swaps, and computes all 24 scores in every control using section-column accumulation. It does not import the producer. It checks **1,199,976 null order scores**, all observed orders, every minimum and tie list, and the full tail count. Every baseline-order control score also matches the earlier section-preserving report. Both implementations share Python's pseudorandom primitive.

The toy tests exhaust small section permutations with unequal section sizes and repeated values. A non-divisible example demonstrates why the cyclic reduction requires complete rows.

From the repository root, choose new output paths:

```sh
python scripts/test_lp1_section_order.py
python scripts/lp1_section_order.py --output order-replay.json
python scripts/check_lp1_section_order.py order-replay.json --receipt order-replay-audit.json
```

The producer checks the frozen input hashes. Compare the replay report's SHA-256 with `report_sha256` in the independent audit receipt. The downloadable result retains the full order mapping, observed scores, all six class scores for every trial, and all minimizing orders; none of the searched arrangements is omitted from that representation.

## Read the figures

The order diagram lists all 24 arrangements in six groups. Every arrangement in one group has the same Q; the bar represents that shared score. Letters label sections, not rune values. The histogram shows the minimum score retained from every complete 24-order search. Its vertical scale counts trials, and its dashed line is the observed minimum. All 49,999 trials are included; the bin counts are downloadable as CSV.

## Run the complete reproduction

Extract the experiment ZIP with folders intact. Run `python experiments/records/lp1-section-order/run.py --check` from its root. Python 3 standard library is sufficient; the run is offline. Use `--output order-replay` to retain results in a new directory. The wrapper repeats the simulation, independently checks every order score, and reproduces the figures and histogram.

See the [fixed-order section-preserving comparison](#/experiments/lp1-section-balance), [original baseline](#/experiments/lp1-word-length-balance), and [search-space explanation](#/wiki/search-space).
