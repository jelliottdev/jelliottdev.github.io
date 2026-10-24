# Historical algorithm diagnostic fixed before manuscript scoring

This run will enumerate the complete source-defined 9,900-case autokey grid. It is not a validated exclusion of autokey ciphers or proof that a correct key would always recover. No target scores have been inspected when this amendment is frozen.

The source's encoder and decoder do not always describe the same process. The plaintext encoder can read the complete future plaintext, whereas the decoder can use only text already recovered. The ciphertext encoder substitutes zero when a requested ciphertext symbol does not yet exist, whereas its decoder reads the complete observed ciphertext at that position. A generated example can therefore be impossible for the matching decoder to recover, even with unlimited beam width.

All 360 outcomes are retained: two known passages, 45 primers, two models and both signs. Independent pointer enumeration finds 54 of 180 P cases and 59 of 180 C cases admit the complete true reading; all 113 recover exactly and retain the truth. All remaining 247 cases make future-key queries in the source encoder and have no true path under the decoder. Some also exceed the decoder's per-transition three-skip limit; this does not substitute for the independent all-path feasibility check. No feasible truth was pruned or outscored in these controls.

The P score gate passes 54 cases, while the C score gate passes 99, including 40 nonexact outputs. Eight wrong-primer C controls also pass. Both original 90-rune source gates pass; the source's full C fixture recovers only about 67% of its known reading. Score passage and complete recovery must remain separate.

For a nonempty primer, the P frontier always leaves a valid no-skip continuation. Thus all source-grid outputs are full-length; the source's short-denominator match formula is a latent API concern, not an observed partial output. The frontier permits at most primer length minus one skipped draws in the whole message. Its 29 singleton P primers permit no skips: 3,190 target labels belong to the rigid P-autokey subset, retained for faithful source enumeration.

The target preserves all 45 distinct primers, both modes/signs, page-local source order, width 450, max_skip 3 and strict score > −5.5. Source cumulative-score winners remain unchanged. A separately labelled diagnostic finds the best normalized score among retained terminal paths; it does not replace the historical winner or examine paths discarded by the beam. No new complete-search null probability is claimed.

Independent native/compiled parity covers 228 synthetic cases and 15,761 ordered terminal hypotheses. Every known-control encoder trace, feasibility result and native beam has also been checked, including 56,063 terminal hypotheses. Original files/controls are frozen. Root explicitly authorized this complete diagnostic target after these receipts and this purpose amendment are bound; no public integration is authorized by the execution itself.
