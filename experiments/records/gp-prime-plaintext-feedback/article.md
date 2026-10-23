## Finding

We tested two precise ways for a newly recovered rune's [Gematria Primus prime value](#/alphabet) to set the next key. Neither stood out in a complete-page search. The best of **6,380** LP2 candidates was on LP2-32, but **144 of 199** matched shuffled-page searches found an English score at least as high. The leading output begins `NGDIAIATTHEWABAETEEAHT...`; this isolated fragment is not a reading.

![Two prime-valued feedback rules and their full-search comparison.](experiments/records/gp-prime-plaintext-feedback/feedback-overview.svg)

The same search recovered all **12 planted full-length messages** made from the archived Warning reading. An independent checker reproduced all 6,380 decoded outputs and scores, checked every shuffled input, and reran three complete null grids. These controls show the bounded test works; they do not prove that every possible autokey would be found.

## The two rules

Let `C[i]` be a ciphertext rune index, `P[i]` its decoded index, and `g(x)` the GP prime value at index `x`, reduced modulo 29. We tried every initial value `s = 0…28` and both signs `e = −1,+1`:

| Rule | Decoding |
| --- | --- |
| Previous plaintext rune | `P[0] = C[0] − e·s`; then `P[i] = C[i] − e·g(P[i−1])` |
| Running plaintext prime sum | Start `S[0] = s`; then `P[i] = C[i] − e·S[i]` and `S[i+1] = S[i] + g(P[i])` |

All arithmetic is modulo 29. Each complete LP2 page starts afresh. Punctuation does not advance the key. We did not delete text, skip runes, reset at words, carry state across pages, or iterate whole-text passes. Those would be different rules; the proposal's imagery of “shedding” does not define one of them.

We defined these two rules to explore numerical autokey. The original proposal did not specify either equation. Each parable number has the same effect as one of the 29 starting values already tested; this test gives none of them a special role. Other records cover [index-valued feedback](#/experiments/feedback-opening-census), [known readings used as a fixed key](#/experiments/solved-reading-running-key), and [partial feedback-table fits](#/experiments/crib-inferred-feedback-table). The [word-boundary replay](#/experiments/dukotah-word-boundary-key-clocks) tests previous-ciphertext prime values and word-level sums. Those are different update rules.

## What the comparison means

We scored the full decoded page for four-letter English patterns, after writing each rune in its standard Latin form. The exact score is average quadgram log likelihood. Each of 199 controls shuffles rune order independently within every page, then repeats **the whole search** over both rules, signs, seeds and pages. This is a conditional check of whether the selected best score is unusual given page lengths and rune counts; a shuffle is not a cipher model. The observed best score was **−6.835**; the shuffled-search median was **−6.760** (larger scores are better). Results and every candidate are available in [results.json](experiments/records/gp-prime-plaintext-feedback/results.json) and [cases.csv](experiments/records/gp-prime-plaintext-feedback/cases.csv).

The test uses the site's 55 nonempty LP2-00–55 transcriptions and one pinned English score model. Another alphabet mapping, language, primer construction, key layer, or stopping rule remains outside this record. No candidate here establishes an LP2 reading or an encryption mechanism.

## Reproduce

The [frozen plan](experiments/records/gp-prime-plaintext-feedback/plan.json) records the equations, inputs, seed range, score and shuffled-control schedule. From the repository root, run `python experiments/records/gp-prime-plaintext-feedback/run.py --check` and `python experiments/records/gp-prime-plaintext-feedback/check.py`. The first uses NumPy and Numba; the independent checker uses only the Python standard library. The saved outputs are also in the experiment ZIP.
