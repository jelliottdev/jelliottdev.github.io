## What this source search actually establishes

Two published searches tried to read a message from **already-decoded Liber Primus text**. One selected every *k*th character or a diagonal from the joined text. The other read the first or last rune of each printed line or word. We replayed the pinned source sweeps: **3,508 selection reads and 48 line/word reads; none crossed the source's final threshold.** That count describes the run. It does not, by itself, establish that these hiding places are empty.

![The four planted examples clear their own length thresholds but fall below the final thresholds.](experiments/records/solved-text-selection-source-gate/gates.svg)

The source tested whether its detector could find a planted message. **All four plants passed a threshold for reads of their own length. None passed the stricter threshold used for the final result.** The controls therefore show that the extraction and first scoring step work; they do not measure the chance that a message of the planted strength would survive the decision rule applied to the manuscript. The source's “control-validated null” wording goes beyond that evidence.

The line/word search had one read just above its own length threshold: a reversed word-last string from the section labelled 06. It was unreadable and far below the final threshold. The source describes one crossing as below an expected 0.048 crossings. It is **above** 0.048; that expectation is not a probability bound, and the 48 reads are dependent. Neither point makes the string a solution.

## Exactly what was searched

The earlier search used 1,754 selectors on Latin letters and 1,754 on rune indices: every-*k* positions, reversals, and diagonal folds. The later search used line-first, line-last, word-first and word-last reads on each of five decoded **source sections** and on their concatenation, in both directions. Those sections span **ten LP1 images**: 01, 05, 06–09, 03–04 and 14–15. The source's five-section order is not manuscript order. These tests did **not** try the unsolved LP2 ciphertext.

Both searches used the source's English quadgram score and 1,000 shuffled-letter controls per length. Its final bar is the highest null score across lengths; the plants were checked against their own length bars. A calibrated replacement would repeat the *entire selection and scoring process* on each null sample and on planted examples, then test whether the plants cross that same final bar. For the line/word version, first check the line breaks against the manuscript images: the source geometry differs from Liberpedia's current LP1 reading exports.

## Check the record

Run `python experiments/records/solved-text-selection-source-gate/check.py` from the repository root. It checks the two pinned [source result files](experiments/records/solved-text-selection-source-gate/source-r22-results.json) and [line/word result file](experiments/records/solved-text-selection-source-gate/source-r23-results.json) against the recorded counts and threshold comparisons. The [earlier replay audit](research/dukotah-r23-a2-source-audit-2026-10-22.md) records the original commands and their observed outputs. To regenerate the null sweeps, use the pinned source scripts linked below; this record does not silently change their geometry, model or rule.
