# All two-rune starts for one feedback rule

The earlier test forced the two starting key values to be equal. Allowing every pair still produced no candidate above the preset English-score threshold. Across 55 pages, the search checked 46,255 combinations of page and starting-key pair; 40 of 49 shuffled complete searches scored at least as highly as the manuscript. This tests one fixed rule, not every autokey cipher or plaintext language.

![The full primer search and why starting errors persist](experiments/records/two-rune-primer-extension/primer-grid.svg)

Rune values here are alphabet indices 0–28, not gematria primes. The rule subtracts the previous two recovered plaintext rune values from each ciphertext rune, modulo 29. The first two positions instead subtract two starting key values. We tried every pair of values from 0 to 28 on each of the 55 nonempty LP2-00–55 source pages, resetting at each page. LP2-50 has no rune stream and is excluded. The first two output runes are omitted before source GP transliteration and English quadgram scoring.

The [earlier multi-history search](#/experiments/public-multihistory-feedback) tried only 29 equal-value starts for this fixed rule. Those 1,595 page/primer cases overlap here; 44,660 cases add unequal starts. Other functions, signs, directions and history lengths in the earlier search are not repeated or completed by this extension.

## Known inputs and the manuscript result

Before target scoring, the complete 841-pair search recovered both the original source control passage and the separate known Warning reading under three unequal starting-key pairs each. The true text ranked uniquely first in all six plants. These are two passages with three starts each, not six independent text samples, and they do not establish power for every possible reading. All 5,046 candidate outputs and scores in these controls matched the unchanged source exactly.

On the manuscript, the best was [LP2-49](#/reader/lp2-49), with starting key values 11 and 8, scoring −6.504 against the −5.5 threshold. Its full output has 66 runes; the scored tail has 79 Latin quadgrams. The best prior equal-start score was −6.557, so allowing unequal starts improved the score slightly but still missed the frozen gate. None of the candidates passed. The 49 controls repeat the entire page-and-primer selection after shuffling each page. They provide a bounded comparison, not a general probability or proof about the cipher.

## Why a wrong start does not disappear

For this exact two-plaintext-rune sum rule, changing the start adds errors that repeat every three positions. If the first two plaintext errors are A and B, the third is −A−B modulo 29, followed again by A, B, −A−B. A wrong start therefore does not automatically “lock on” after a short transient. This identity justifies faster evaluation without dropping any of the 841 starts; it does not apply to every feedback recurrence.

## Evidence and reproduction

The frozen plan, all score arrays, 55 best-per-page outputs, 40 leading outputs and 49 shuffled-search maximum witnesses are retained. The whole target plus null search took 7.24 seconds on the recorded machine. An independent direct recurrence and separate string-based scorer checked all 46,255 manuscript outputs and scores with exact agreement; the 49 null maxima were also reconstructed. The checker does not independently rescore every nonwinning shuffled candidate.

From the extracted bundle root, run the quick byte/arithmetic check or the complete isolated replay:

```text
python experiments/records/two-rune-primer-extension/quick_verify.py
python experiments/records/two-rune-primer-extension/replay.py
python experiments/records/two-rune-primer-extension/check_algebra_portable.py
python experiments/records/two-rune-primer-extension/plot.py --check
```

Python 3.12.10, NumPy 2.5.4 and Numba 0.67.0 are the recorded environment. The bundled requirements list packages; scripts do not install them. Replay stages unchanged scientific files in a temporary directory, reruns controls and the entire target/null grid, independently checks results and compares deterministic values plus exact score-file bytes. Timings and hashes of timing-bearing reports are handled separately; expected files remain unchanged.

Dukotah’s source decoder, scorer, source control and transcription are pinned at revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`, with their exact source license retained. This is a new bounded primer extension, not a replay of a source unequal-primer campaign. English scoring, page boundaries, the fixed sum rule and no skipping are substantive limits; no new decipherment is claimed.
