# Reading every nth rune

**Question.** Does taking every *n*th rune, at some starting phase, reveal English when the counter restarts on each page or runs across the book?

**Result.** No tested setting stands out. The best score came from **step 24, phase 2, restarting on each page**: take zero-based positions 2, 26, 50 and so on, which are the third, twenty-seventh and fifty-first runes. Its 563 selected runes scored **−7.151** under the fixed English model. In **182 of 256** shuffled-page controls, the *best* of the same 868-setting search scored at least as well (global add-one estimate **183/257 ≈ 0.712**). The output is not a reading; it begins `EBNGHITHJTHLDU|MBHEASSTHGEAAX|UPNEOINWAEN…`, where bars mark page boundaries.

![The best observed every-n score sits within the range of complete shuffled searches and below their median.](experiments/records/fixed-step-position-extraction/full-search-scores.svg)

## What was searched

We used the **12,956** archived GP runes on LP2-00–55, excluding the empty LP2-50. For each step **2 through 29**, we tested every phase from **0 through step − 1**. Twenty-nine is a declared upper bound from the size of the GP alphabet, not evidence of a cipher period. Each phase was tried with two clocks: reset to position zero at every page, or continue through all pages joined in numerical order. That makes **868 settings** of one method family. Punctuation and layout never advance the counter.

We converted each selected rune to its canonical GP Latin label and scored English four-letter groups. With the page-reset clock, each page's selected text was scored separately and those score sums pooled; no four-letter group crossed a page boundary. All **868** settings supplied at least **360** within-segment four-letter groups and cleared the preregistered 100-group minimum. A valid reading in another language or under a second cipher layer would not necessarily score well here.

To judge a whole phase search fairly, each control trial shuffled the rune order **within every complete page once** and reused those same 55 shuffled pages for all 868 settings. This preserves each page's rune frequencies while disrupting position-specific text. The comparison is between the **best observed setting** and the **best setting in each trial**, not between an attractive observed phase and an average random phase. The median control maximum was **−7.122**, slightly above the observed −7.151. As a sensitivity check, all **868** synthetic controls with known GP reading indices planted at the selected positions recovered those indices exactly and cleared the frozen English-recognition threshold; their lowest score was **−4.509**.

The test covers forward fixed steps 2–29 with these two page clocks and direct English scoring. It does not test periods beyond 29, reversed streams, transposition after selection, number-derived keys, other languages, or arbitrary rules chosen after viewing the output. The source idea list suggested every-*n* extraction but did not specify a historical search to replay.

## Inspect and reproduce

[`streams.tsv`](experiments/records/fixed-step-position-extraction/streams.tsv) contains **all 868 exact extracted streams** as runes and Latin labels, with `|` showing page boundaries. [`results.json`](experiments/records/fixed-step-position-extraction/results.json) contains every observed score and all 256 complete-control maxima. From the repository root, run `python experiments/records/fixed-step-position-extraction/run.py --check` and `python experiments/records/fixed-step-position-extraction/check.py`; both require NumPy and Numba. The second script independently reads the page JSON, rebuilds every stream, and recomputes all observed scores and 256 full searches with a different quadgram implementation.
