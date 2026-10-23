# Do these pages reveal a repeating key length?

Two checks in Wulfic's archived [session 17 program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/session17_clean_solve.py) look for a repeating key period. They **both detected a planted period of 13**, but neither gives convincing evidence for a period in the tested LP2 pages.

![The known-plaintext lag check found no LP2 result above its report line. The split-column check flagged about as many LP2 pages as a typical complete shuffled search.](experiments/records/wulfic-session17-period-detectors/comparison.svg)

**Check 8** tries eight fixed passages as possible plaintext on **LP2-04–17**. At each sampled alignment, it asks: “If this were the plaintext, would the implied key repeat after a prime number of runes?” The strongest LP2 match repeated at **10 of 76 positions**—**13.2%**, below the source's **greater than 25%** report rule. None of the **4,239 distinct passage/alignment searches** crossed that rule. Twelve of 49 complete shuffled searches reached at least the observed best fraction. The source calculates both subtraction and addition implied keys, but one is the negative of the other, so their equality-at-a-lag evidence is identical; these are **8,478 source settings, not 8,478 independent ideas**.

**Check 9** needs no guessed plaintext. On **LP2-04–37**, it splits each page into columns according to candidate prime periods, then compares the columns' rune repetition with the whole page. Its stated line flagged **29 of 34 pages**. That looks broad until the same complete scan is repeated after shuffling every page: the middle of 49 shuffled searches also flags **29 pages**, and **26 of 49** flag at least as many. The largest single LP2 column-to-page ratio was **2.28**; **5 of 49** shuffled whole scans reached it. The source also lists factors of distances between repeated trigrams, but sets no acceptance threshold for those factors, so they are preserved as descriptive data, not treated as separate hits.

The planted control used the source's own P03 candidate text and a fixed 13-value repeating key. Check 8 ranked that exact period and text alignment first, with **248 of 248** lag pairs equal. Check 9 flagged period 13 on the planted page. Yet Check 9 also flagged **27 of 34** seeded uniform control pages, showing that its 1.3× page-baseline line is permissive in this grid. The plant tests whether these detectors can register a clean periodic construction; it does not calibrate every language, page length or interrupted cipher.

The [plan](experiments/records/wulfic-session17-period-detectors/plan.json) pins the exact source passages, offsets, prime periods, page mapping, thresholds and 49 shared full-search shuffles. [Results](experiments/records/wulfic-session17-period-detectors/results.json) retain all page/period values, the complete known-plaintext reports, Kasiski summaries and each shuffled maximum. The [control result](experiments/records/wulfic-session17-period-detectors/control-results.json) was written before checking LP2. The old source page numbers **21–54** map to the site's **LP2-04–37**; all 34 pinned rune streams match the site rune for rune.

We also ran the unchanged pinned source script with its exact page files in a temporary directory. Its Test 8 printed **no strong periodicity**, and its Test 9 marked exactly the same **29 pages**. The [source execution receipt](experiments/records/wulfic-session17-period-detectors/source-replay.json) hashes the complete stdout after normalizing line endings to LF. This matches the source's printed verdicts; our saved tables make its underlying measurements and full-search controls inspectable.

These are period *screens*, not decryption tests. Check 8's authored passages could differ from any intended text, and its sampled alignments can miss an untried alignment. Check 9's highest ratios often occur at long periods with short residue columns. The 49 shuffles preserve each page's rune counts but do not model an encryption algorithm; the fractions above are descriptive full-selection comparisons, not universal probabilities. Other periods, boundaries, transcriptions, layers and changing key clocks remain outside scope. A separate [LP2-31 test](#/experiments/lp2-31-periodic-ioc) used one page, periods 2–20 and a different pooled coincidence statistic.

To reproduce, supply a separate Git checkout containing the pinned Wulfic revision; its unlicensed source is not copied into the experiment bundle:

```text
python experiments/records/wulfic-session17-period-detectors/run.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT --check
python experiments/records/wulfic-session17-period-detectors/check.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT
python experiments/records/wulfic-session17-period-detectors/replay_source.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT --check
python experiments/records/wulfic-session17-period-detectors/plot.py --check
```

The runner verifies exact source and page bytes. Its independent checker counts matching modular differences at each lag directly and enumerates equal rune pairs within split columns, then repeats the complete planted and shuffled searches without importing the runner.
