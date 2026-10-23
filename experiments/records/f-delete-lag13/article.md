## Finding

Deleting every F rune does **not** reveal an unusual lag-13 two-rune repeat under this fixed test. The archived LP2-00–55 stream has **17** exact matching two-rune blocks at lag 13. After deleting all **458 F runes** within their pages and joining the retained neighbors, the count is **18**. In **499** page-preserving shuffle trials, the middle 95% of counts is **8–22**, and **104** trials reach at least 18.

![Lag-13 exact two-rune matches before and after removing F, with the shuffled reference.](experiments/records/f-delete-lag13/comparison.svg)

The displayed counts have different numbers of opportunities: **12,186** before F deletion and **11,728** afterward. The fixed lag-13 result is therefore best read beside its own shuffled reference, not as a one-count improvement by itself.

## Full lag search

The program also repeats the same exact-block test at every lag from **2 through 28**. It divides each observed count by that lag's mean under shuffled pages, then compares the largest ratio with the largest ratio from every shuffled trial. The observed best is **lag 5**, with a ratio of **1.707**; **109 of 499** shuffled searches do at least as well. Lag 13 was proposed in the discussion, but the broader scan guards against quietly choosing another attractive lag afterward.

## Rule and limit

This test interprets an “F skip” as deleting **every** F (GP index 0) from the rune-only stream, independently on each page. It does not say that the source participant used this deletion rule. Their account did not specify whether F is copied, removed, or consumes a key slot. Nor does this test model collision-driven skips, I/M resynchronization or a key stream. It tests only whether this one removal operation exposes exact two-rune repeats at the proposed lag.

Run `python experiments/records/f-delete-lag13/run.py --check` from the repository root. The [saved report](experiments/records/f-delete-lag13/results.json) retains per-lag counts, reference means, input hashes and the seed so the comparison can be reproduced.
