# Do LP2 sections share a running key?

If two rune streams use the **same additive key at the same position**, subtracting their ciphertexts cancels that key. A [published source test](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/tests5.py) measured whether the resulting differences look more structured than chance across nine LP2 sections and many relative shifts. This record replays that calculation and checks its strongest alignments.

## Finding

![A cross-section peak of 6.01 sits almost on the shuffled-search median of 6.03; 53 of 99 shuffled complete searches reach at least the observed score.](experiments/records/leo-shared-key-differences/cross-section-control.svg)

The strongest alignment **between different sections** is pages 3–7 against pages 33–39, shifted by 25 runes with 1,120 runes overlapping. Its normalized difference score is **6.01**. After seeing that result, we ran a separate whole-search control: shuffle rune order within each of the nine sections, then search all 36 distinct section pairs and every eligible shift again. **53 of 99** shuffled searches reached at least 6.01; their median maximum was **6.03**. This is an exploratory, post-observation comparison, not a discovery probability fixed in advance. The observed cross-section peak does not stand out under this control.

The source also included each section paired with itself. Under the pinned current code, the largest all-pair score is **11.32**, from adjacent runes within pages 40–53. It is a local difference-pattern measurement, not evidence that two sections share a key. None of 99 whole-section-shuffle searches reached this self-pair score, which confirms the local ordering signal but does not identify its cause. The manuscript's uneven difference distribution and word structure are plausible contributors; this test does not separate them.

## Why the archived numbers differ

The source's saved [result printout](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/results/tests5.txt) lists pages 15–22 against pages 33–39 as its top pair at shift 1,598, overlap 305, score **3.3**. That *same* alignment has score **5.68** under the standard-deviation formula in the pinned `lp.py`. Applying an approximation of `0.75 / √n` to its unchanged difference count gives **3.25**, which rounds to the archived 3.3. This shows a numerical inconsistency between the saved printout and the pinned current formula. The approximation is one possible explanation; we have not established which code version or formula produced the printout.

The source's synthetic example is a useful positive control. Two known rune texts encrypted with one shared key have difference IoC **1.047**; 300 source-style unaligned comparisons average **1.000**. Kappa also rises from a null mean of **0.0367** to **0.0592**. The statistic can detect this planted relationship at that length. It does not imply the LP2 sections have it.

## Method and limits

The [frozen plan](experiments/records/leo-shared-key-differences/plan.json) names the nine exact section files, the 1,200-rune synthetic example, all 45 unordered pair scans (including nine self-pairs), every shift with at least 300 runes overlapping, and 99 full-search shuffles. The [post-observation plan](experiments/records/leo-shared-key-differences/followup-plan.json) explicitly filters to 36 different-section pairs. Results and every selected alignment are [saved](experiments/records/leo-shared-key-differences/results.json); the [follow-up results](experiments/records/leo-shared-key-differences/followup-results.json) preserve all 99 control maxima. An [independent check](experiments/records/leo-shared-key-differences/check.py) recomputes each reported winning window directly and verifies both source receipts.

Shuffling entire sections breaks real short-range rune structure, so the control answers a conditional question about this scoring/search procedure. It does not test every possible key reset, transposition, cipher layer or alignment. A high difference score alone is not a decryption.

## Reproduce

The source text is a separately pinned [relikd transcription](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4); the scripts verify every input SHA-256. With that checkout at `REL` and the pinned Leo source checkout at `LEO`, run from the repository root:

```text
python experiments/records/leo-shared-key-differences/run.py --source-root REL --check
python experiments/records/leo-shared-key-differences/followup.py --source-root REL --check
python experiments/records/leo-shared-key-differences/check.py --source-root REL --source-test-root LEO
python experiments/records/leo-shared-key-differences/plot.py --check
```

The full search uses NumPy and Numba; the independent window checker uses Python's standard library. The source license allows reading and checking, but this record does not copy its implementation.
