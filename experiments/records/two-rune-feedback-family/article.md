# Two-rune feedback with every starting pair

Trying every starting pair across seven fixed two-rune feedback functions produced no candidate above the preset English-score rules. But known-input checks also showed that the highest-scoring output is not always the complete true text. This is a bounded score-screening result, not a rejection of autokey ciphers.

![Whole-family score screening and its known-input limit](experiments/records/two-rune-feedback-family/family-score-screen.svg)

Each rule derives the next key value from the previous two recovered rune values, or from those values combined with the corresponding ciphertext values. Rune values here are alphabet indices 0–28, not the gematria primes; some functions then use their prime values. We tried all 841 ordered starting-key pairs on each of 55 nonempty LP2-00–55 pages. The first two output runes are omitted before GP-to-Latin expansion and English quadgram scoring. Empty LP2-50 supplies no rune stream.

## What the search found

The best output was on [LP2-51](#/reader/lp2-51), using plaintext-history last-difference feedback, subtraction, forward order and starting values 9 and 16. Its score was -6.164, below the absolute −5.5 threshold. Its complete output contains 92 runes; the scored tail has 117 Latin quadgrams. It is a retained candidate, not an established reading.

Every shuffled control repeats the entire family search after independently shuffling the rune order within each page. Thirty-five of 49 whole-family maxima scored at least as highly as the manuscript. The strongest shuffled maximum was -5.830; the frozen rule also required a margin of 0.5 above that, making the combined gate -5.330. No candidate passed. These are whole-family comparisons, not separate probabilities for each branch or a general significance claim.

## What the known-input controls do and do not show

The two known passages were the original source control and the separately documented Warning reading. Across three unequal starting pairs and all branch labels, all 336 supplied true keys recovered their text exactly and scored above −5.5. The complete search selected the whole true output in 264 of those constructed cases. The unique-truth-first diagnostic passed 216; another 88 had tied maxima without a better alternative, and 32 had a higher-scoring alternative.

All 88 tied cases retained the true scored tail under the deterministic selected output. Forty changed only the two unscored starting positions. The higher-scoring alternatives changed scored positions too. Every failure is retained. These counts reuse only two passages and dependent directions/aliases; they are not 336 independent language samples. A passing score does not establish exact recovery or a decipherment.

The imperfect identification diagnostic was recorded before target scoring. A separate purpose amendment authorized the fixed score-screening enumeration with those limits intact. No branch, control text, scorer or threshold was replaced to obtain an easier pass.

## Scope, overlap and exact duplicates

The seven source functions are sum, prime-value sum, XOR, prime-of-sum, prime-of-prime-sum, last difference and alternating sum. Plaintext and mixed histories, both signs and both input directions give 56 labels. At two-rune history, last difference and alternating sum duplicate one another after sign reversal and negating both starting-key values. Exhaustive pair tables and source parity establish 48 effective branches; the original labels and stable tie order remain visible.

The grid contains 2,590,280 labelled settings, representing 2,220,240 effective settings. The [original restricted-primer search](#/experiments/public-multihistory-feedback) already covers the equal-start cases; the [single-rule primer extension](#/experiments/two-rune-primer-extension) adds one unequal-start branch. Their union overlaps 133,980 labelled settings here. The additional scope is 2,456,300 labelled settings, or 2,099,020 effective settings. Settings are not counted as distinct solving ideas. Every branch was recomputed uniformly; no prior scores or null panels were reused.

Other history lengths, functions, boundaries, skips, alphabets and language models remain outside this experiment. The previous restricted-seed result for three-rune plaintext/mixed history is not repaired by a two-rune extension.

## Check or repeat the calculation

The complete observed effective score matrix, per-page/per-label maxima for all 49 shuffled searches, top 40 observed outputs, per-label best outputs, global shuffled witnesses, exact inputs and source hashes are retained. The original producer took 417.3 seconds. A separate checker uses direct formulas and raw-table language scoring; it reconstructs the whole observed matrix and all retained null maxima. Its full null-grid reconstruction is explicitly sampled, rather than a second calculation of every discarded shuffled candidate.

From the extracted bundle root:

```text
python experiments/records/two-rune-feedback-family/quick_verify.py
python experiments/records/two-rune-feedback-family/replay.py
python experiments/records/two-rune-feedback-family/plot.py --check
```

The quick check validates saved bytes, matching shuffled inputs, alias ordering and gate arithmetic without running decoding searches. Full replay stages a fresh temporary directory, reruns all original control outcomes and the complete target plus 49 whole-family searches, checks independent formulas, and compares deterministic values and exact numeric bytes. Expected results stay unchanged. Runtime may vary.

The recorded environment is Python 3.12.10, NumPy 2.5.4 and Numba 0.67.0. Package pins are provided separately; scripts install nothing and make no network or model calls. Source code and source scoring inputs are from Dukotah/cicada3301 revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. The exact source license is bundled; its MIT grant for original work excludes third-party puzzle material and community transcriptions.
