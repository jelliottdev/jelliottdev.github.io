# A keyword that shifts with each rune

The archived [advanced cipher program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/advanced_cipher_solver.py) assigns one keyword to each of ten pages, then changes that keyword's shift at every rune. We replayed **all nine steps on each page**. No output establishes a reading. The strongest source word score was **86** on LP2-11; **10 of 199** complete shuffled searches scored at least as high.

![The strongest manuscript source word score is 86, compared with 61 at the middle and 95 at the highest of 199 complete shuffled searches. A known-reading plant recovered exactly and scored 380.](experiments/records/wulfic-keyword-ramp/comparison.svg)

The rule is simple: take the keyword's rune value at position *i*, add *i* times a fixed step, and subtract that total from ciphertext modulo 29. Each page restarts at position zero. The source's steps are **1, 2, 3, 5, 7, 11, 13, −1, and −2**. For example, with CABAL and step 7, the key begins `5, 2, 2, 16, 19, 11…`. This is a repeating keyword plus a steady position ramp, not a plain progressive Caesar shift.

We checked the source scoring path before the manuscript sweep. Encrypting the complete, established **209-rune first-koan reading** with CABAL and step 7, then testing all nine steps, recovers every rune only at step 7. That true candidate ranks first under the source score, at **380**. It demonstrates power for this clean example, not for every possible reading or language. The source score counts selected English substrings in a run-together GP transliteration; it is a rough screen and can reward accidental fragments.

The ten pinned source rune files numbered **21–30** match the site's **LP2-04–13** arrays rune for rune. Each of the 199 seeded controls shuffles each page once, retains its original keyword, tests all nine steps, and saves the highest score across the entire ten-page search. The shuffles keep each page's rune frequencies but destroy its order; they are a selection reference, not a cipher model. The source script's other autokey, running-key, F-skip and LFSR branches are separate questions, many already tested in bounded records. These nine steps do not exhaust other keywords, step schedules, boundary resets, or layered methods.

The [plan](experiments/records/wulfic-keyword-ramp/plan.json) fixes the exact branches, pages, known-reading control, and shuffle procedure. The [results](experiments/records/wulfic-keyword-ramp/results.json) give all 90 candidate scores and decoded-output hashes plus 199 full-search control maxima. From the full checkout or experiment bundle, with an exact checkout of the public Wulfic revision supplied separately:

```text
python experiments/records/wulfic-keyword-ramp/run.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT --check
python experiments/records/wulfic-keyword-ramp/check.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT
python experiments/records/wulfic-keyword-ramp/plot.py --check
```

The original source has no license in that checkout, so the bundle does not copy its script. The runner executes its exact key and score functions from a SHA-256-checked Git blob. The independent checker rebuilds the arithmetic, all outputs, the known-reading plant and all shuffled maxima without importing those functions.
