# Uniform additive keys: exact adjacent-match comparison

## Status and prior knowledge

Prepared replication, not a new discovery or blinded test. The archived transcription's 86 within-page doublets and the external closure register's C04 claim were known before this plan. The count was selected because it was already discussed as unusually low. Any computed tail is conditional on the stated model, not corrected for the historical search across manuscript features.

## Fixed inputs and statistic

Use the archived LP2-00–55 text files and the 29-rune alphabet. Include headings; remove non-runes; keep every page boundary; count all overlapping equal-neighbor pairs. Empty pages contribute zero edges. Recount the number of rune positions, nonempty pages, edges and doublets rather than entering the historical totals as constants. Compare the recount with the existing coordinate ledger and verify its source hashes.

## Model and proof obligation

For any fixed plaintext, let `c_i = p_i + k_i mod 29`, with mutually independent keys uniform on all 29 residues and independent of the plaintext. Ciphertext positions are then independent uniform symbols. For each page, the transformation from its ciphertext to its first symbol plus successive modular differences is bijective. Consequently those differences are independent uniform residues, even though adjacent-pair events share ciphertext positions. Equality is exactly a zero difference. If the total number of within-page edges is E, the total number of equal neighbors has distribution `Binomial(E, 1/29)`.

This argument requires uniformity. It does not establish independent neighboring-match events for arbitrary nonuniform symbol frequencies or for a shuffle conditioned on fixed rune counts.

## Calculation and controls

Report the observed count D, the exact expected count E/29, variance E×28/29², and the inclusive lower-tail probability `sum(comb(E,j) × 28**(E-j), j=0..D) / 29**E`. Sum with integer arithmetic and render the ratio with declared high-precision decimal arithmetic. Preserve hashes of the exact integer numerator and denominator, plus enough information to reconstruct both. Do not substitute a normal approximation or report a rounded probability of zero.

Independently recount the archived streams and calculate the same finite tail through the recurrence between successive binomial masses. Exhaust small uniform alphabets and short page-length configurations to verify the full adjacent-match distribution, including shared endpoints, separate page anchors and empty pages. Include a nonuniform three-position counterexample demonstrating why uniformity matters.

Show the null distribution with the observed count clearly separated from its main mass. Label both axes, the fixed alphabet and page-boundary rule. Retain a readable numerical result alongside the figure. The figure must not imply that a low probability identifies a cipher or plaintext language.

## Boundary of the conclusion

This tests one statistical model. A rare event is not logically impossible. Nonuniform, dependent or plaintext-dependent keys, output filtering, altered boundaries and other cipher equations remain outside it. In particular, the multiplicative running-sum model in the doublet guide has different assumptions and must not be rejected with this binomial result. No formal-proof-system rerun is claimed. Human review remains pending after computational checks.
