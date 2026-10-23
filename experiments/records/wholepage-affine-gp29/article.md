## Result

**No fixed affine map made a complete unsolved LP2 page resemble the archived English readings.** We tried every invertible map of the 29-rune alphabet on each of **55 rune-bearing pages**: **44,660 page/map outputs**. None reached the fixed English-score threshold of −5.5. The best, on LP2-55 with `P = 12C + 22 (mod 29)`, scored **−6.543**.

That winner is ordinary for a search this large. We shuffled rune order separately within every page, reran the **entire 44,660-output search** 199 times, and kept each trial's highest score. **144 of 199** trials matched or exceeded the manuscript maximum. The result limits this particular static-alphabet English reading; it does not eliminate changing alphabets or other ciphers.

![The best LP2 affine score falls among the full-search shuffled controls, far below the weakest complete known reading.](experiments/records/wholepage-affine-gp29/scores.svg)

## What the search covers

For each archived rune index `C`, the proposed plaintext index is `P = aC + b (mod 29)`. We tested **all 28 nonzero multipliers** and **all 29 offsets**. Because 29 is prime, each of these 812 maps permutes the alphabet. They include all constant shifts (`a = 1`) and ordinary Atbash (`a = 28, b = 28`) without listing those cases twice. Each map acts uniformly across one complete page, including headings. LP2-50 has no runes and contributes no candidate.

Before scoring LP2, we tested the scorer and search on all **nine complete archived readings**. All nine scored above −5.5 and above 99% of 200 rune-order shuffles of their own text. We also constructed a ciphertext for each reading whose intended decoding map was `P = 7C + 13 (mod 29)`; the search ranked the planted true plaintext first among 812 maps **nine times out of nine**. These controls show the procedure can recover a similar English reading if this sort of map generated it. They do not establish English as the language of every unsolved page.

The shuffled controls preserve each page's rune frequencies and length. Comparing **global maxima** accounts for selecting the most attractive page and map after seeing all results under this positional null. A rune shuffle is not a simulation of Cicada's possible encryption process. The 44,660 outputs are parameter settings within one method, not 44,660 independent ideas.

## Reproduce and limits

The [plan](experiments/records/wholepage-affine-gp29/plan.json) pins all 56 page transcriptions, nine reading traces, alphabet and score model by SHA-256. The [complete case ledger](experiments/records/wholepage-affine-gp29/cases.jsonl) gives every page, map, score and decoded-index hash; the [summary and null maxima](experiments/records/wholepage-affine-gp29/results.json) are separate. Run `python experiments/records/wholepage-affine-gp29/run.py --check`, then `python experiments/records/wholepage-affine-gp29/check.py` for an independent reconstruction. Both use NumPy and Numba for the full search; the runner crosschecks fixed cases against a separate ordinary Latin-string scorer.

This does not test a map changing by position, word, line or page state; arbitrary substitutions; transposition; alternate rune assignments; hidden layers; or non-English plaintext. The visible text may also require more than one operation.
