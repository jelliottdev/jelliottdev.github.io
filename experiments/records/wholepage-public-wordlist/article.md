# Public wordlist keys on complete LP2 pages

## Finding

None of the **43 archived rune keys**, tested at every phase and in both GP29 arithmetic directions, made a complete rune-bearing LP2-00–55 page reach the predeclared English-score threshold. The best output scored **−6.50**. In a matched control that reran the entire search after shuffling rune order within each page, **105 of 199** searches found a score at least that high. This does not identify an English reading from this key list.

![Best complete-page score from the public keys alongside the median full-search shuffle result and the weakest genuine solved-reading control.](experiments/records/wholepage-public-wordlist/score-comparison.svg)

The earlier [public key replay](#/experiments/public-wordlist-vigenere) checked exact openings at phase zero. Here every phase of each of the same **43 fixed keys** is used to decode every rune on each of **55 pages**; LP2-50 has no runes. That is **618 key, phase, and direction settings** and **33,990 complete-page outputs**. This is one bounded extension of the public wordlist, not 33,990 independent ideas. Of the two keys in the earlier [known-key whole-page test](#/experiments/wholepage-known-vigenere-keys), `welcome` is exactly source key 43; `second-koan` is absent from this wordlist.

## What the score means

The score averages English four-letter log likelihoods over the canonical Latin transliteration of each decoded page. Larger values look more like the archived English controls. All nine genuine solved-reading examples passed the predeclared −5.5 threshold and beat at least 198 of 200 individual shuffled controls. All nine planted encipherments were recovered as the highest-ranked setting among the same 618 candidates. The best actual LP2 output stayed below −5.5; **none** of the 33,990 outputs reached it.

The 199 full-search shuffles address selection: with this many pages and key settings, the single highest score will look better than an ordinary random output. A shuffle preserves each page's rune counts and length while disrupting its order. The observed best score was near the middle of the shuffled full-search maxima. A shuffle is a comparison device, not a model of Cicada's encryption. This result does not exclude a different key, a word reset, a second layer, a different alphabet, or a non-English plaintext.

## Reproduce

The [frozen plan](experiments/records/wholepage-public-wordlist/plan.json) declares exact input hashes, score, controls and global null before the LP2 run. [Results](experiments/records/wholepage-public-wordlist/results.json) include all 199 null maxima; [cases](experiments/records/wholepage-public-wordlist/cases.jsonl) retain every output score and decoded-rune hash. Run `python experiments/records/wholepage-public-wordlist/run.py` from the repository root to regenerate them. `python experiments/records/wholepage-public-wordlist/check.py` independently reconstructs every decoded-rune hash, sampled portable scores and three separated full-search null maxima. The run uses Python, NumPy and Numba.
