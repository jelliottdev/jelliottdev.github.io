# Keyword skip sweep: independent pretarget source review

Source revision: `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. No manuscript scoring was performed for this review. Exact file hashes and independently extracted counts are in `static-receipt.json`, produced by `static_review.py --source-root PATH --output FRESH.json`.

## Exact executable scope

`liber-primus/analysis/campaign18_skip/armada2/keywords_skip.py --full` first requires its source gate, then `full_run()` calls **attack_page_keyword_fast**. It does not call `attack_page()` or the generic two-tier prefilter, despite adjacent comments discussing that alternative.

Ordered raw groups: CICADA_VOCAB, ESOTERIC_VOCAB, COMMON_WORDS, PUZZLE_VOCAB, SHORT_KEYS. Deduplication is by stripped uppercase spelling before greedy GP encoding. Seven two-letter GP transliterations take priority; V/K/Z/Q alias to U/C/S/C indices. Other characters are dropped. This is not an arbitrary Latin alphabet or a 4,000-word list: the implemented full list has 623 labels, 617 exact arrays, and 2,814 labelled phases. On 55 source segments, two signs and two Atbash flags give 619,080 phase screens and 137,060 best-phase decisions.

`load_pages()[:-2]` is source-segment numbering, not a claim of physical pages 00–54. The established source mapping excludes empty LP2-50 and extends through LP2-55; its exact input hashes must be rebound before any target.

The 90-rune screen uses `min(90,L)` and width 300. For each keyword/sign/Atbash/segment, strict `>` updates retain the first source phase if normalized screen scores tie. Only that selected phase is rerun on the complete segment at width 500 if its screen score is strictly above −6.0; a returned full score strictly above −5.5 is a source hit. Nonselected phases are not full-length tests. An output crossing a scorer gate is a candidate, not a plaintext confirmation.

## Decoder invariants and aliases

The exact decoder is `sweep.beam`, max skip 3. It initializes the first output with no initial skip, then tries accepted positions `previous+1+d` for d=0,1,2,3 in that order. Every rejected key position must produce the preceding ciphertext rune under the proposed current plaintext. This is an admissibility rule, not a likelihood weighting by 0.83. Atbash changes ciphertext to 28−C before this rule.

Source sort is stable descending cumulative canonical Latin quadgram score; the final winner is the first cumulative maximum. Acceptance uses score divided by the number of Latin quadgrams. Different GP expansions have different Latin lengths, so cumulative and normalized ordering need not agree. Preserve this behavior, then report an explicitly separate final-terminal-beam normalized audit for every full survivor. Neither reading only the returned winner nor this retained-beam audit proves anything about pruned or nonselected hypotheses.

For segment length L, `need=4L+64`; `tile_key` returns `floor(need/P)+2` copies of P symbols. The latest required source buffer check is `phase+4L+8`, with phase≤17. The periodic key therefore covers the entire decoder bound without zero padding. Actual last accepted key position is at most phase+4(L−1).

Six exact encoded spelling aliases are AS/AZ, SO/ZO, CA/KA, CE/KE, SA/ZA, SE/ZE. Rotating the encoded arrays gives 2,721 distinct arrays; including sign and reducing fundamental periods gives 5,420 distinct infinite signed streams. These are aliases inside one experiment, not extra methods or a reason to silently change labelled tie/order reporting. EA, EE, IA, OE, OO and TH encode to constant keys. With constant keys, skipped positions cannot change the plaintext relation; rigid/substitution overlap must be disclosed. Atbash is retained separately.

## Control acceptance questions before target

1. Replay the original source gate unmodified: CIRCUMFERENCE, sign −1, phase 0, no Atbash, source fixed plaintext/seed. Its declared gate is recovery >95%, beam score >−5.0, and rigid/wrong-key scores <−6.0. Report exact recovery separately; do not retroactively replace that gate.
2. Source/optimized decoder parity must cover native screen/full lengths and widths, both signs/Atbash, nonzero phases, repeated-key/constant-key and tie-heavy cases. Preserve exact stable tie order and initialization, not only close scores.
3. Known-reading plants should cover the 617 encoded arrays and consequential phase/orientation choices under a fixed pretarget seed policy. Separate true-key admissibility, true-phase screen success, selected-phase promotion, full gate passage and exact recovery. A wrong selected phase can block a valid planted full output even when the true phase passes its own screen.
4. The source encoder can reject more than three keys because its loop is unbounded. Any bounded-seed selection rule must be declared first and report failures/zero-skip cases, or independently establish an alternative admissible truth path. Do not silently retry until success or discard failed controls.
5. Original English score thresholds are historical source constants, not a new whole-search significance calibration. Broad OTP, rigid-Vigenere exclusion and family-rejection assertions in source prose are not conclusions of this finite replay. Failed sensitivity or ranking controls must remain visible and may require a diagnostic-only purpose amendment before target.

Producer protocol/control plan review is pending. This note is not pretarget clearance.
