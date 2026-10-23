## Finding

**The lag-35 peak is real in the transcription, but it is not unusual once the search over 242 lags is counted.** On LP2-00–02, 42 of 694 rune pairs separated by 35 positions are equal, a standardized score of **3.759** against a uniform 29-rune reference. It is the largest score among lags 1–242. Yet **82 of 999** step-shuffled controls have a peak at least this large after undergoing the *same* 242-lag search (one-sided plus-one proportion **83/1,000**).

![The lag-35 score is in the upper, but ordinary, part of the best-of-242 control distribution.](experiments/records/lp2-00-02-lag35-selection/selection.svg)

## Why the search matters

[A public analysis](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/lag_and_parity_tests.py) reported lag 35 as the highest coincidence score in the 729-rune opening section and observed no repeated peaks at 70, 105 or 140. That arithmetic reproduces here. If **35 had been specified before looking**, none of our 999 controls would reach its score at that fixed lag. But 35 was selected as the strongest among 242 candidates; the comparison must select the strongest lag in every control as well.

| Lag | Equal pairs | Standardized score |
| ---: | ---: | ---: |
| 35 | 42 / 694 | 3.759 |
| 70 | 22 / 659 | −0.155 |
| 105 | 26 / 624 | 0.983 |
| 140 | 22 / 589 | 0.382 |

The controls keep the exact inventory of all **728 modular differences between adjacent runes**—including four zero steps, the section's adjacent doublets. Each trial shuffles those differences, reconstructs a 729-rune stream from the original first rune, scans lags 1–242, and retains its largest score. The strongest control scores range from **2.007 to 5.318**; their median is **2.950**. This is a conditional reference for the observed step composition, not a simulation of the manuscript's encryption. The [results](experiments/records/lp2-00-02-lag35-selection/results.json) include all 242 observed lag counts and all 999 maxima.

## What the test can say

There is no convincing **period-35 recurrence by this coincidence statistic**. A genuine repeating key could leave a peak at 35 or a harmonic, but a weak or interrupted one might not. The absence of harmonics here is descriptive; it does not rule out every interrupted, changing or compound key. The control scan only corrects for choosing among these 242 lags in this section. It does not adjust for choosing the section itself, alternative transcriptions, scoring rules, or many other ideas tried elsewhere.

As a basic power check, the script plants a 35-periodic 29-symbol sequence with 55% of positions independently replaced. Its strongest scanned lag is 35, with z **29.139**. This is deliberately easy to detect; it verifies the code can recognize a substantial planted recurrence and does not establish power for subtle ones.

Reproduce offline with `python experiments/records/lp2-00-02-lag35-selection/run.py --check`, then run `python experiments/records/lp2-00-02-lag35-selection/check.py`. The independent checker recounts the manuscript peak and rebuilds the first ten controls through a separate pair-count calculation. Both scripts use Python's standard library and the archived transcription.
