# Can a simple substitution fit a proposed opening?

**One of 495 fixed page-and-opening pairs fits a single, one-to-one rune substitution.** LP2-12 can be paired with the archived second-koan opening under this rule. That fit assigns 10 of the 29 rune mappings and leaves **19! = 121,645,100,408,832,000** complete substitution keys. It fixes only five of the next twelve positions. A compatible opening is therefore not a reading of the page.

![One compatible page opening assigns ten rune mappings and fixes five of the following twelve positions.](experiments/records/monoalphabetic-crib-capacity/continuation.svg)

The twelve numbered boxes represent positions 13–24 after the proposed opening. Blue marks positions whose ciphertext rune appeared in the first twelve, so the proposed mapping determines their output. Gray positions use a ciphertext rune not yet assigned; their outputs are still free. The boxes do **not** display verified plaintext.

## What was checked

We paired the first 12 runes of each of the 55 rune-bearing unsolved LP2 pages with each of nine openings fixed from the [archived known readings](#/experiments/lp2-known-vigenere-keys). Headings count as runes; spaces and punctuation do not. LP2-50 contains no runes and is excluded. The rule is one permutation of the 29 Gematria Primus symbols for a whole page: every occurrence of a ciphertext rune maps to the same plaintext rune, and two different ciphertext runes cannot map to the same plaintext rune.

That rule gives a direct consistency check. If a crib contradicts either mapping direction, no substitution key fits it. If it consistently assigns *m* distinct ciphertext symbols, the other 29 − *m* outputs can be permuted in **(29 − *m*)!** ways. The first twelve positions were used for the fit; the following twelve were used only to count which positions would already be determined.

| Fixed comparison | Result |
| --- | ---: |
| Page starts × proposed openings | 55 × 9 = 495 |
| Incompatible equality patterns | 494 |
| Compatible patterns | 1 |
| Next twelve positions fixed in that case | 5 |

The lone fit is an **algebraic possibility**, not evidence that the second koan occurs on LP2-12. There is no independently known LP2 continuation to compare with its five forced outputs. The 19! keys also disagree on the remaining seven positions. Other words, later alignments, page-specific key changes and more complex ciphers were not tested.

## Reproduce

The [plan](experiments/records/monoalphabetic-crib-capacity/plan.json) fixes the inputs and rule. Run `python experiments/records/monoalphabetic-crib-capacity/run.py --check`, then `python experiments/records/monoalphabetic-crib-capacity/check.py` from the repository root. The independent checker reconstructs every page from its JSON transcription and verifies all 495 counts with a separate pair-set calculation. It also exhaustively enumerates 2,118 small-alphabet cases and checks a planted 24-rune known reading. The full [case results](experiments/records/monoalphabetic-crib-capacity/results.json) retain each page/crib outcome.

This is a bounded test of **simple substitution at page starts**. It does not eliminate substitution with a different plaintext, placement or preprocessing rule, and it does not identify a cipher for LP2.
