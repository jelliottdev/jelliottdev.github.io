# Can one LP2 page decode another?

**Question.** If two ciphertext pages are aligned from their first rune, does adding or subtracting their GP rune indices produce English?

**Result.** None of these direct readings stands out. The highest score came from **LP2-18 minus LP2-02** across their first **201 runes**. Its GP labels start `GCIREOONGSNGEASIAJABUSDFPNGEOR…` and score **−6.802** under the fixed English model. In **193 of 256** matched searches on shuffled pages, the best pair and operation scored at least as high (global add-one estimate **194/257 ≈ 0.755**). The displayed output is not a reading.

![The first five arithmetic steps in the strongest pair, followed by its score within the range of complete shuffled searches.](experiments/records/lp2-page-pair-english/pair-scores.svg)

## What was tested

We paired every two distinct rune-bearing pages from **LP2-00–55**, excluding empty LP2-50: **1,485 page pairs**. For each pair we aligned rune ordinal zero with rune ordinal zero and stopped when the shorter page ended. The three operations were **A + B**, **A − B**, and **B − A**, always modulo 29. A sum needs only one page order; for English scoring the two subtraction directions can read differently. This gives **4,455 candidate streams**. We translated each output index to its canonical GP Latin label and scored English four-letter groups. **4,136** streams cleared the predeclared minimum of 100 groups; shorter ones were not treated as negative results.

The diagram shows the first five steps of the strongest candidate. For instance, LP2-18 begins with index 28 and LP2-02 with 22; **28 − 22 ≡ 6 (mod 29)**, whose GP Latin label is `G`. The other four displayed differences become `C I R E`. This is arithmetic on the transcribed runes, not a claim that the pages were meant to be paired.

To account for choosing the best pair after seeing thousands of outputs, every control trial shuffled all 55 pages once and ran the **same complete pair-and-operation search**. Each page was shuffled in bands set by the observed page lengths, preserving the rune histogram of every prefix that any pair compares. All pairs in a trial shared those shuffled pages. The median control maximum was **−6.749**, higher than the observed −6.802. Three synthetic controls planted a known decoded GP reading into each arithmetic operation; each recovered the intended indices exactly and scored **−4.478**, well above the fixed English-recognition gate.

This extends the [earlier page-pair test](experiments/records/lp2-page-pair-alignment/article.md), which measured symbol concentration rather than readability. It covers only **zero-offset, nonrepeating, forward page arithmetic** and direct English scoring. It does not test shifted alignments, a repeating page key, reversal, additional cipher layers, other languages, or page pairings selected by a separate manuscript clue. Catalog item **7.3** supplied the idea; it did not identify a documented historical experiment to replay.

## Inspect and reproduce

[`results.json`](experiments/records/lp2-page-pair-english/results.json) includes all **4,455** observed case scores, the complete best output and all **256** global control maxima. From the repository root, run `python experiments/records/lp2-page-pair-english/run.py --check` and `python experiments/records/lp2-page-pair-english/check.py` (NumPy and Numba required). The independent checker reads structured page JSON instead of the producer's text files and recomputes the whole observed and shuffled search with a separate scoring loop.
