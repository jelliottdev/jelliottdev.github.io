# Solved manuscript readings as a running key

**Question.** Can the eight established readings of Liber Primus serve, in order, as a key that reveals a complete unsolved page?

**Result.** No complete reading was established. The best of **292,318** whole-page alignments used 66 runes of LP2-49 and had an English score of **−5.897**. That exceeds the best scores from all 16 shuffled versions of the same key and four GP-encoded windows of unrelated English. It is a signal to investigate, not a reading: the resulting text begins `EOAHIAEOSMASTHOOHYSOEMUNEADEALT…`. A short, selected page can score well by chance or by a feature the controls fail to model.

![The solved-reading key scores above the two limited reference groups, but yields no readable page.](experiments/records/solved-reading-running-key/key-comparison.svg)

## The test

We joined **2,892 runes** from eight established readings in manuscript order: Warning, Welcome, Some Wisdom, First Koan, Loss of Divinity, Second Koan, Instruction and LP2-57. These are their recorded Gematria Primus indices, not an English transliteration. For each of the **55 rune-bearing pages LP2-00–55** (LP2-50 has no rune text), we tried every contiguous key position that could cover the *entire* page, with both addition and subtraction modulo 29. The key did not wrap, skip, or restart at word breaks. We scored each complete output with the same pinned English quadgram model; the highest score across the whole grid was the reported result.

The 16 controls each shuffled the **whole 2,892-rune key once**, then searched the same page/offset/sign grid. Their highest scores ranged from **−6.426 to −6.070**; none reached the observed −5.897. Sixteen trials give only coarse resolution: the add-one global estimate is **1/17**, about **0.059**, and the shuffle removes the real key's language and structure. It cannot establish that the solved readings uniquely explain LP2.

As a separate *post-observation* check, we converted four nonoverlapping windows of the archived Emerson text into GP indices using one frozen greedy rune rule, then searched the identical grid. Their maxima ranged from **−6.430 to −6.150**. This small comparison also leaves many other structured keys untested; it is not part of the 16-trial probability estimate. An earlier ASCII-letter version of this plan was superseded **without being run**, because ASCII indices would not match the GP-index key.

Before looking at LP2, we encrypted the complete 184-rune Warning reading using a First Koan key segment, with Warning excluded from the *control key*. The same full search recovered the correct offset, sign and every rune. This avoids matching the control plaintext to itself. Warning remains part of the actual eight-reading LP2 key.

The result only covers this ordered source, direct additive GP29 arithmetic, all fitting offsets, and complete pages under one English model. A high score without a coherent plaintext and independent continuation is not a decryption. It does not eliminate other source orderings, key derivations, page subsets, interrupted clocks, or languages.

## Reproduce

From the repository root, run `python experiments/records/solved-reading-running-key/run.py --check` for the portable full computation (Python 3 standard library). Install NumPy and Numba to run `python experiments/records/solved-reading-running-key/fast_check.py`, which independently checks the same complete grid with a numeric scorer and compares six arbitrary nonwinning cases to the portable scorer. `english_key_control.py` reproduces the separate Emerson diagnostic with those optional libraries. `plan.json`, both diagnostic plans, `results.json`, and the pinned source traces document every input and bound.
