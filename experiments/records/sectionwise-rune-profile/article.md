# Do the final LP2 pages have different rune statistics?

The last two pages, LP2-54–55, have **308 runes**. We compared their rune collision rate and adjacent repeats with the preceding LP2-40–53 section. A direct comparison of all 3,008 earlier runes with 308 ending runes would conceal how much these measures fluctuate at the shorter length, so the main reference is **every 308-rune window** of the earlier section.

**Both ending values fall inside the middle 95% of those earlier windows.** This is a useful check against a conspicuous simple change in these two measures. It neither proves the sections use the same construction nor rules out different keys, transforms or page-specific instructions.

![Two horizontal scales show the final pages' collision and doublet rates inside the central range of equal-length windows from pages 40–53.](experiments/records/sectionwise-rune-profile/comparison.svg)

| Measure | LP2-54–55 | Middle 95% of LP2-40–53 windows | Earlier windows at least as high |
| --- | ---: | ---: | ---: |
| Rune index of coincidence | 0.03382 | 0.03302–0.03655 | 1,892 of 2,701 |
| Equal adjacent runes, within pages | 3 / 306 = 0.98% | 0.33–1.63% | 759 of 2,701 |

*Index of coincidence* (IoC) is the chance that two rune positions contain the same symbol. Its near-uniform reference for a 29-rune alphabet is 1/29 ≈ 0.03448. A *doublet* is two equal runes adjacent after non-runes are removed within one page; page joins do not count. The 2,701 reference windows overlap heavily, so “windows at least as high” is a descriptive position among windows, **not a p-value** or 2,701 independent trials. The doublet count of three is also small enough that the rate is unstable.

## Section overview

The section boundaries below follow the artwork grouping used for this comparison. They are not independently established cipher boundaries. LP2-50 contains no runes and contributes nothing to the rune measures.

| Pages | Runes | IoC | Doublets / within-page pairs |
| --- | ---: | ---: | ---: |
| 00–02 | 729 | 0.03408 | 4 / 726 |
| 03–07 | 1,145 | 0.03463 | 6 / 1,140 |
| 08–14 | 1,729 | 0.03446 | 9 / 1,722 |
| 15–22 | 1,903 | 0.03450 | 10 / 1,895 |
| 23–26 | 1,021 | 0.03427 | 11 / 1,017 |
| 27–32 | 1,433 | 0.03419 | 13 / 1,427 |
| 33–39 | 1,680 | 0.03436 | 12 / 1,673 |
| 40–53 | 3,008 | 0.03454 | 18 / 2,995 |
| 54–55 | 308 | 0.03382 | 3 / 306 |

These are measurements of the archived rune transcription, not a classification of cipher types. The page ranges were chosen for their visible section organization; selecting another split after seeing these numbers would require its own declared test. The window comparison conditions on the composition and order of the earlier section. It does not simulate a cipher or account for the many possible ways to divide the manuscript.

## Reproduce

From the repository root, using Python 3.12 and its standard library:

```text
python experiments/records/sectionwise-rune-profile/run.py --check
python experiments/records/sectionwise-rune-profile/check.py
```

The [plan](experiments/records/sectionwise-rune-profile/plan.json) fixes the group boundaries, measures and equal-length comparison; [results](experiments/records/sectionwise-rune-profile/results.json) contain exact counts and input hashes. `run.py` without `--check` regenerates that JSON; `plot.py` redraws the figure. The independent checker uses direct rune-pair enumeration instead of the producer's frequency counter. For the complete 86-doublet source-location ledger and separator sensitivity, see [doublets](#/wiki/doublets) and [doublet boundaries](#/experiments/doublet-boundaries).
