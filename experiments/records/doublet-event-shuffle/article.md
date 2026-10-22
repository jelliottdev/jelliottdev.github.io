# Do the reported doublet-event patterns survive better controls?

An earlier report extracted repeated adjacent runes from unsolved LP2 and described large GP distances between consecutive doublet symbols, concentrations at distances 5, 12 and 14, and a forward +4 difference at event lag three. The [event recount](#/experiments/doublet-event-lags) pins the 86-symbol sequence and finds a lag-one mean of 734/85 ≈ 8.635, rather than the reported 8.81. This companion record checks the reported patterns against two different shuffle controls. Neither control simulates a cipher; both ask what ordering could arise while holding specified aspects of the observed event inventory fixed.

![Two histograms compare the observed lag-one distance sum of 734 with global and within-page event shuffles.](experiments/records/doublet-event-shuffle/shuffle-controls.svg)

## Inputs and fixed statistics

The input is the exact [86-event ledger](experiments/records/doublet-event-lags/results.json) from LP2-00–55. Each event represents one adjacent equal-rune pair. For runes with indices *a* and *b*, the forward difference is `(*b* − *a*) mod 29` and the minimum circular distance is `min(d, 29 − d)`. Event lag counts places in this extracted list, not places in the manuscript. Event comparisons may cross a page boundary; doublets themselves were found only within pages.

The three source-specified measurements are the lag-one circular-distance sum **734** over 85 pairs, **31** lag-one distances in bins 5, 12 or 14, and **10** forward +4 matches among 83 lag-three pairs. We compare them with 20,000 seeded shuffles of the 86-event multiset. In a second control, each page retains its own event symbols and event count, but their order within that page is shuffled. The latter tests whether the apparent signal is largely due to different pages containing different sets of doublet runes.

| Source-specified statistic | Observed | Global shuffle: draws ≥ observed | Within-page shuffle: draws ≥ observed |
| --- | ---: | ---: | ---: |
| Lag-one circular-distance sum | 734 | 31 / 20,000 | 3,910 / 20,000 |
| Lag-one distances 5, 12 or 14 | 31 | 5 / 20,000 | 879 / 20,000 |
| Lag-three forward +4 | 10 | 13 / 20,000 | 23 / 20,000 |

The middle 95% of the global-shuffle lag-one sum is **545–694**; for within-page shuffles it is **648–767**. The observed 734 falls inside the latter interval. Therefore the broad “doublet events are farther apart” observation depends strongly on whether page-specific rune inventories are preserved. The +4 count stays unusual under these two narrow controls, but it was noticed after inspecting the data.

## Selection matters

The source report singled out lag three and +4, as well as a set of three circular-distance bins. For a more realistic post-selection check, each shuffle can choose its own largest directed-difference bin from **all 29 bins at lags one through three**, and its own largest three-bin circular-distance total over those lags. The observed maxima are 10 and 31, respectively.

| After allowing that choice | Global shuffle: draws ≥ observed | Within-page shuffle: draws ≥ observed |
| --- | ---: | ---: |
| Largest directed bin at any of lags 1–3 | 1,123 / 20,000 | 3,510 / 20,000 |
| Largest three circular-distance bins at any of lags 1–3 | 4,434 / 20,000 | 9,653 / 20,000 |

This correction covers **only** those stated choices. It cannot account for all distances, statistics, transcriptions, page subsets or ideas someone may have considered before reporting a pattern. Thus the narrow +4 result should be treated as a lead for a prediction on untouched data, not as a cipher finding. The original report's permutation p-values cannot be reproduced exactly without its event list, implementation and randomization policy; these are new seeded calculations on the archived transcription.

## Reproduce

Run `python experiments/records/doublet-event-shuffle/run.py --check` to regenerate all 40,000 shuffles and verify every saved count. `check.py` independently recounts the three observed statistics from the pinned event ledger and checks the published Monte Carlo denominators. The [plan](experiments/records/doublet-event-shuffle/plan.json), [complete results](experiments/records/doublet-event-shuffle/results.json) and figure script are included in the experiment download. Tail estimates use `(count + 1) / (20,000 + 1)`; a small Monte Carlo fraction is not a probability that any proposed decryption is true.
