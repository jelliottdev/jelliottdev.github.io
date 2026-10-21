# Bounded key-search maxima: fixed protocol

## Question

How does the best English score change when a declared key search grows? This follows the scorer and decoder controls. Their outcomes are already known. No local scores for this experiment have been calculated. This protocol is project-level preregistration, not an externally registered or blinded study.

## Fixed source and model

Use all nine known-reading CSV traces and their first min(240, available) output rune indices, exactly as in decoder controls. Retain all sections without removing hash or other non-prose material. Use the same 29 canonical transliteration labels and frozen English quadgram model. Score the mean log10 count probability over overlapping four-letter groups, unseen count 0.01, acceptance threshold −5.5. The measure is a heuristic English score, not a plaintext probability.

## Search space

Use SHA-256 counter-mode key fixtures as specified in decoder controls: ASCII `liberpedia-decoder-control:<seed>` followed by a four-byte big-endian counter starting at zero, each digest byte reduced modulo 29. Keep 240 slots, with no repetition, offsets, skip rules, sign changes or extra transformations. The byte reduction is biased and is part of the declared fixture.

The wrong-key dictionary is seed IDs 0 through 255 in ascending order. Report every nested prefix budget: 1, 4, 16, 64, 256. Candidate p[i] = (c[i] − key[i]) modulo 29. At each budget retain the maximum normalized score, breaking exact score ties by the smallest seed ID. Keep every individual score and its candidate rune-sequence SHA-256 hash (one byte per 0..28 index). No language-dependent or page-dependent adjustments.

## Controls and repeated searches

For each of the nine section lengths and each replicate ID 0..31, create:

* A null ciphertext of independent `randrange(29)` draws from a fresh Python Random instance seeded with `33010000 + 1000 * section_index + replicate`. This is reproducible pseudorandom data from a specified null generator, not an assertion that the manuscript is random.
* A positive ciphertext by adding the known rune prefix to the derived key with seed `100000 + replicate`, modulo 29. That seed is deliberately absent from the wrong-key dictionary.

Score all 256 wrong keys on both ciphertexts. Separately decode the positive ciphertext with its true key and verify exact rune recovery. For each prefix budget, also record the winner after appending that true key: this is a search of **budget + 1** candidates, not the original budget. Record both score acceptance and exact recovery; a correct key need not win under every heuristic score. The true-key index is never used to select among the wrong keys.

The full grid has 9 × 32 = 288 paired searches and 147,456 wrong-key candidate scores, plus 288 true-key controls. Save all outcomes. No adaptive stopping, seed expansion or threshold adjustment is allowed. Reused source sections, dictionaries and lengths create dependence. These are not 288 independent texts or estimates of a universal false-positive rate.

## Reporting and interpretation

For each section, show all five budget conditions and the observed range and median of its 32 null maxima. Also publish every per-search maximum, positive search with the true key absent, and positive search with the true key appended. Include integer counts exceeding the fixed threshold and exact-recovery counts. Do not convert the results into a probability that a manuscript candidate is correct. Do not pool sections into a single claimed population accuracy or publish only the most striking section.

Within each search, maxima cannot decrease as the nested dictionary grows; verify this invariant. The positive truth score is invariant across budgets, and inclusion and omission of the true key must remain separate. The experiment demonstrates and measures selection under this specific finite search. It does not calibrate beam searches, adaptive choices, other key families or human selection among decoded phrases.

## Verification

Freeze source hashes before scoring. Use an independent checker with no imports from the producer to rebuild source prefixes, key bytes, nulls, every candidate index/hash and score, all winners and tie rules, and exact positive recovery. A small exhaustive fixture must test tie selection and nested maxima. Preserve the full plan, scripts, outputs and checker receipt in the eventual download. Human review remains separate from computational replay.
