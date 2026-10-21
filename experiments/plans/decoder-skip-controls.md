# Planted decoder controls: fixed protocol

## Question and prior knowledge

Does a decoder recover known rune indices when its key-alignment rules match the encoder, and what happens when they do not? This follows the pinned Dukotah review, not a claim that Liber Primus uses any of these constructions. Its reported outcomes were known before this plan. No local benchmark scores have been inspected.

Separate three questions: whether the true path is permitted by the decoder, whether beam pruning retains it, and whether the final candidate receives a high language score. A high score does not substitute for exact recovery. The earlier English-scorer experiment already demonstrates language-dependent acceptance.

## Inputs and selection

Use all nine existing known-reading CSV traces in the manifest. Take the first min(240, available) output rune indices from each, preserving their order. Do not convert edited English back into runes. Keep every section, including the LP2-56 hash material if it falls within the prefix. These are known-index controls, not nine independent samples of ordinary prose. Retain exact endpoints and hashes. Use the canonical 29-label transliteration solely for scoring; exact recovery compares indices.

Use seed IDs 0, 1, 2. Generate bytes from SHA-256 of ASCII `liberpedia-decoder-control:<seed>` followed by a four-byte unsigned big-endian counter starting at zero. Reduce each byte modulo 29 and retain 10,000 values. This reduction is biased (256 is not divisible by 29); it is a reproducible key fixture, not a uniform random pad. The second key condition repeats each generated value four times, then truncates to 10,000 slots. Wrong-key controls use seed + 1000 under the same generator and repetition rule. No offset search: all begin at zero. Exhaustion is an error, never zero padding.

## Encoder variants, all retained

Arithmetic is modulo 29, with ciphertext c = p + k and plaintext p = c − k. Reset at each independent section/seed/variant. The first emitted rune has no preceding ciphertext and cannot trigger suppression.

1. **Rigid addition:** consume exactly one key slot per plaintext rune.
2. **Key skipping:** when a proposed ciphertext rune equals the previous emitted rune, reject the key slot if a local Python Random instance draws randrange(100) < 83. A rejection consumes one key slot and retries the same plaintext rune. Draw only on equality. PRNG seed is 3301 + seed ID, reset for each plant. Record every rejected and accepted slot.
3. **Value rewriting:** consume exactly one key slot; on equality and the same draw rule, emit (proposed ciphertext + 1) modulo 29. Record the rewrite. This is a different encoder, not a skip variant that a skip-only decoder is expected to invert.
4. **One unrelated advance plus key skipping:** immediately before plaintext position floor(length/2), consume one additional key slot, regardless of the doublet rule. Then use variant 2. Record the unrelated advance separately.

All mechanisms are operationally specified fixtures. None is fitted to manuscript frequencies, IoC, entropy, or doublet rate. Similar surface statistics alone would not make a fixture a validated model of the manuscript.

## Decoders and selection

For each plant, run the correct and wrong key through rigid subtraction and through four beams: widths 16 and 64 crossed with maximum skips 1 and 3. The first position uses key slot zero. At each later position, try advances 0 through the maximum skip count, in ascending order. For candidate plaintext p at the accepted slot, every skipped slot must satisfy p + skipped key = previous ciphertext. This is a transition constraint, not knowledge of the random suppression draws. It permits accepting a repeated ciphertext because suppression is probabilistic. It does not permit arbitrary advances.

Score each beam prefix by the cumulative log10 English quadgram score of its canonical transliteration, using the frozen model from English-scorer controls. Break equal scores by the lexicographic accepted-slot path, then plaintext indices. Retain the highest-scoring declared beam width without deduplication. At the final step choose by that same rule; also report the normalized score. This intentionally separates the search's cumulative criterion from its reported normalized score. Multi-letter rune labels make those criteria different; no claim of optimizing normalized score is made. No early stopping or threshold-based pruning.

Report the true path's transition validity, first invalid step, and first beam-pruning step when it was admissible. An admissible path is not guaranteed to win. All plants retain the best returned candidate even when wrong. Record exact match, matching-index count/length, longest correct prefix, candidate indices and key slots, cumulative and normalized score, score acceptance at −5.5, and complete encoder trace. A trace-assisted oracle verifies the recorded encoder operations but is explicitly not an attack available to a solver.

There are 9 sections × 3 seeds × 2 key fixtures × 4 encoders = 216 plants, with ten decoder/key-condition results per plant. Keep all 2,160 results, including failures. No manuscript sweep or large dictionary search follows automatically.

## Verification and publication

Before the benchmark, test tiny alphabets exhaustively: direct subtraction, recorded-key inversion, skip constraints and ambiguity. Check constant runs, multiple rejections, first-position behavior, rewrite wraparound, exhaustion and an unrelated advance not representable by the transition rule. An independent checker must reconstruct each encoder trace and each returned candidate, recompute scores, and replay beam selection without importing the producer. Check the complete declared grid and all frozen input hashes.

Publish both exact recovery and score acceptance, grouped by encoder and decoder bounds. Show both key fixtures and every section/seed; aggregate counts are descriptive and not independent-trial accuracy estimates. Distinguish structural exclusion from beam-pruning loss. This is a fresh controlled benchmark, not replication of the source repository's percentages, proof of a manuscript cipher, or evidence for an unrecoverable pad. Human review remains a separate step.
