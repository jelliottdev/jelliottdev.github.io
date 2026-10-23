# Do short spans repeat at lag 13?

A reported idea describes repeated rune patterns in 10–15-rune windows at lag 13, perhaps in connection with an interrupted cipher stream. It does not supply the original windows, positions, or a rule for what counts as a repeat. This record tests **one precise interpretation**: a 15-rune span whose first two runes match the two runes 13 positions later.

**We found 17 such spans in LP2-00–55.** The exact expectation from independently shuffling the runes within each page is 14.1; 499 full page-shuffle runs commonly produced 7–22. The observed count is within that range. This test does not substantiate an unusual lag-13 excess under this rule, and it does not reproduce or refute a different pattern the original author might have meant.

![Observed count of 17 repeated two-rune patterns at lag 13, within the middle 95 percent of page-shuffle counts from 7 to 22.](experiments/records/short-window-lag13/comparison.svg)

For a span `C₀ … C₁₄`, the test requires **C₀ = C₁₃ and C₁ = C₁₄**. There are 12,186 eligible within-page 15-rune windows in the archived transcription. A 10–13-rune window has no rune pair 13 positions apart; a 14-rune window has one such pair; a 15-rune window has only two. Thus a short attractive-looking example gives little independent evidence on its own. We count *all* eligible windows, not a hand-picked example.

| Check | Result |
| --- | ---: |
| Repeated two-rune spans at lag 13 | 17 |
| Exact expectation under fixed page counts | 14.12 |
| Middle 95% of 499 page shuffles | 7–22 |
| Shuffles with at least 17 | 111 of 499 |

The claim mentioned lag 13 and other potentially important lags. To show the cost of selecting a lag after inspecting the manuscript, the [plan](experiments/records/short-window-lag13/plan.json) also scans **all lags 2–28** for the same repeated-two-rune rule. Lag 13 is not the highest: its observed-to-expected ratio is 1.20, while lag 5 gives the largest ratio, 1.91. When every shuffled manuscript gets the same best-of-27 search, **30 of 499** shuffles reach or exceed that best observed ratio. Even this control only covers those 27 exact-pattern tests; it does not adjust for trying other motif definitions, page ranges, window rules or marker choices.

Shuffling retains each page's rune counts and length but destroys its original order. The result is conditional on that reference, the archived transcription, and the exact two-rune definition. No key sequence, F-skip rule, collision skip or I/M marker is tested here. Those would require complete transition and reset rules, plus a predicted output distinct from the statistic used to select them. See the [doublet ledger](#/wiki/doublets) and [short-lag equality profile](#/experiments/doublet-lag-profile) for related but different events.

## Reproduce

Using Python 3.12 and its standard library from the repository root:

```text
python experiments/records/short-window-lag13/run.py --check
python experiments/records/short-window-lag13/check.py
```

The producer repeats the seeded 499-shuffle comparison and checks it against [saved results](experiments/records/short-window-lag13/results.json). The independent checker parses the archive separately and verifies every observed count through direct two-position slice comparison. The figure is regenerated with `python experiments/records/short-window-lag13/plot.py`. Neither checker can recover the unspecified original windows from the screenshot.
