# The 1,814-rune section pairing

**Result.** The printed-order pairing scores above the median of the shift controls, but it is not isolated: **107 of 1,813 nonzero circular shifts** score at least as high after the same four-way choice. That is a conditional rank of **108/1,814 (5.95%)** when the printed alignment is included. It does not yield a reading or establish a key.

![The printed pairing scores above the shift median but is matched or exceeded by 107 shifted pairings.](experiments/records/section-1814-pairing/comparison.svg)

This is a variant of the [1,894-rune pairing](#/experiments/section-1894-pairing). Only the input streams change. The published section counts give **753 + 747 + 314 = 1,814** runes for Koan 1, Loss of Divinity and Koan 2 after removing every F. Sign Post and Spirals give **695 + 1,119 = 1,814** under the same omission. We reconstructed those streams in printed order from LP1-06–15 and LP2-00–07; the first stream uses the *runes*, not the known English reading.

At each position, we add or subtract the two zero-based rune indices modulo 29. We also try the same operations with the second stream reversed. The complete output is scored by its index of coincidence (IoC), and the highest of the four scores is kept. The best printed-order variant is **reverse, add**: 114,642 ordered equal-rune pairs, or IoC **0.034859**. The median best-of-four score among shifted controls is **113,934**.

The control circularly shifts the second stream through *every* other alignment, applying all four operations and selecting the best each time. It accounts for choosing among those four operations **at this fixed pair of sections**. It does not account for choosing this equality from the source sheet, trying other section combinations or judging candidate plaintext after inspection. The modest upper-tail position is therefore a reason to specify a predictive decoding rule, not evidence that the pairing solves an LP2 page.

Run `python experiments/records/section-1814-pairing/run.py --check` and `python experiments/records/section-1814-pairing/check.py` from the repository root. The [plan](experiments/records/section-1814-pairing/plan.json) freezes the four operations and control; the [result file](experiments/records/section-1814-pairing/results.json) includes all 1,814 shift scores. The independent checker rebuilds the streams and selected scores from the archived transcriptions.
