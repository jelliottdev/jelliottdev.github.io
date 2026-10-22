# Does a Möbius-of-totient zero survive a known LP2 decoding?

A reported LP2-00 reading proposes a necessary rule: if the ciphertext rune has Möbius value zero after applying Euler's totient to its Gematria Primus prime, the plaintext rune at that position must also have zero. That is a checkable statement, separate from the proposed sentence. This control applies the same rule to **LP2-56**, whose [published reading](#/page/lp2-56) uses a uniform one-step subtraction in the 29-rune alphabet. It does not test the author's selected LP2-00 words or claim that LP2-00 uses the same cipher.

For a GP prime value *p*, Euler's totient is φ(*p*) = *p* − 1. The Möbius value μ(*p* − 1) is zero exactly when *p* − 1 contains a squared prime factor. A ciphertext zero therefore has a simple, independently checkable definition. For example, J has GP prime 37; φ(37) = 36 and μ(36) = 0. LP2-56's known shift maps its rune index 11 (J) to index 10 (I), whose prime is 31; μ(30) = −1. That is a counterexample to the stated one-way zero rule at rune position 1 (counting from zero).

![Möbius zero-mask mismatch counts under all 29 fixed shifts on LP2-56. The published one-step shift is highlighted.](experiments/records/mobius-zero-mask-known-page/mismatches.svg)

## Fixed input and result

The script reads the [archived LP2-56 transcription](#/reader/lp2-56) and the stored GP alphabet. It keeps all 85 rune symbols in manuscript order, discards non-rune punctuation and the printed hexadecimal hash, and computes μ(*p* − 1) for each symbol. The decoded index is `(cipher index − 1) mod 29`. We count zero-to-nonzero failures separately from nonzero-to-zero changes; only the first direction is required to refute the reported one-way condition.

| Check on the published shift | Positions |
| --- | ---: |
| Ciphertext zero → plaintext nonzero | **28 / 85** |
| Ciphertext nonzero → plaintext zero | 22 / 85 |
| Either zero-state changes | 50 / 85 |

The first one-way failures, at zero-based positions 1, 3 and 7, are J→I, S→X and L→M. The saved result lists every position and the 29-rune Möbius table. As a comparison, the script applies every fixed shift 0–28 to the same input. The identity shift has zero mismatches by construction; that is a positive calculation check, not evidence for a cipher. The published shift is highlighted in the figure.

## What this closes

The zero-preservation rule is **not an invariant of known Liber Primus decoding**. It fails on a solved page even in the one-way form stated in the report. That does not logically disprove a special rule for LP2-00, and a chosen candidate phrase can still satisfy a zero mask accidentally. To assess LP2-00, a future test needs the exact proposed rune-by-rune plaintext, a fixed spelling/segmentation policy, the full count of admissible alternatives, and an untouched continuation or independent control. The source report's semantic filtering and unattached code files do not establish those bounds.

Run `python experiments/records/mobius-zero-mask-known-page/run.py --check` to reproduce every shift and mismatch position. `check.py` independently identifies zero values by searching for squared divisors; it confirms 28 one-way failures. The [plan](experiments/records/mobius-zero-mask-known-page/plan.json) pins both inputs by SHA-256, and [results.json](experiments/records/mobius-zero-mask-known-page/results.json) provides the complete comparison. The report being evaluated is catalogued under [reported attempts](#/wiki/reported-attempts), with its source-text hash and replay limits.
