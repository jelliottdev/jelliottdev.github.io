# English scorer: language and preprocessing controls

## Purpose and provenance

This is a scorer-only follow-up inspired by Dukotah/cicada3301 at commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. Its paper and language-control script have been read and their reported direction is known. This is not a blind test or a replay of its beam decoder. No scores on the samples below have been inspected before this plan.

Use the pinned English quadgram count table and its documented score: mean base-10 log probability over overlapping four-letter windows, with unseen count floor 0.01 divided by the model's total count. Reimplement the formula locally; do not run the external repository's scripts. Preserve the exact count table, license and source attribution. Validate that every model key is four ASCII capitals and every count is a positive integer, with no duplicate keys.

## Samples and controls fixed before scoring

Use the same eight FLORES evaluation translations already in Liberpedia. Divide their 1,012 aligned sentences into eight consecutive blocks: four blocks of 127 sentences, followed by four of 126. Keep these identical sentence ranges for every language. Join sentences inside a block with a space before normalization.

Test two explicit representations: (1) uppercase then keep only ASCII A–Z, matching the external scorer's filter; (2) uppercase, NFD-decompose, remove Unicode combining marks, then keep ASCII A–Z. Save character counts before and after filtering and the letters discarded by each mode. This is not a phonetic translation into runes. Do not silently transliterate remaining non-ASCII letters or add language-specific rules.

For each language, block and representation take the first 120, 240 and 400 retained letters. Preserve every cell and the exact normalized excerpt with its SHA-256. If a block is too short, stop and report the unmet input condition; do not substitute a different passage. There are 384 cells. Equal-length prefixes begin in aligned passages but may end at different content positions across languages. The nested lengths and shared blocks are not independent trials.

For every cell score the unchanged text, then 20 deterministic character permutations preserving its letter counts. Use a local Python Random instance per permutation with seed `3301000 + 100000*language_index + 10000*block_index + 1000*representation_index + 100*length_index + replicate_index`; indices are zero-based, language order is the original baseline plan, and replicate index is 0–19. Report all permutation scores, their range and mean, and strict-below/equal/strict-above counts relative to the original score. Do not turn twenty permutations into a calibrated significance claim.

Report acceptance at the source's historical `score >= -5.5` threshold for original and shuffled text separately. Do not tune the threshold, floor, model or excerpt length after inspecting results. This threshold belongs to this exact score/model; do not transfer it to an unrelated scorer.

## Interpretation

All original inputs are known corpus text. No decryption is being attempted: text is supplied directly to isolate the scoring stage. A below-threshold original is a rejection of that normalized sample by this particular English scorer, not evidence of a failed decryption or that the language is absent from LP. A passing shuffled control is also retained. Report all eight languages with the same visual treatment and all six representation/length combinations.

Training-set overlap has not been independently excluded; do not claim held-out language-model accuracy. FLORES is translated web text, not genre-matched LP prose. These controls cannot independently reproduce the external paper's recovery-power percentages, which depend on different corpora, rune conversion, cipher and decoder settings. A later encoder/decoder experiment must fix those additional components separately.

## Verification

Before publication, require input hashes, complete excerpts and all scores, an independent scoring implementation using quadgram frequency counts, explicit checks of the normalization rules, and reproduction from the isolated download. The independent implementation should compare numerical scores within a declared absolute tolerance of 1e-12 and verify every threshold decision. Human review remains pending after computational checking.
