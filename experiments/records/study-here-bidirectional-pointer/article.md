# Does 331 / 133 point uniquely to STUDY HERE?

**Result.** On the archived 464-word solved LP1 sequence, forward word **331** is STUDY and reverse word **133** is HERE. The reverse position is forward word 332, so the two directions pick adjacent words. The phrase appears at **five** positions in this already-decoded text, not only at the reported 331 / 133 split. At the selected cut, the final 133 cipher words have the reported Gematria Primus (GP) sum **26,893**. The first 331 sum to **72,065**, which is **102 above** the reported 71,963.

![A line marks the five locations of STUDY HERE in the 464-word reading; the chosen 331/133 split is highlighted with the two measured GP block sums below.](experiments/records/study-here-bidirectional-pointer/pointer-locations.svg)

| Forward STUDY word | Reverse HERE word | First block GP sum | Remaining block GP sum |
| ---: | ---: | ---: | ---: |
| 196 | 268 | 42,503 | 56,455 |
| 227 | 237 | 48,700 | 50,258 |
| 262 | 202 | 56,114 | 42,844 |
| 293 | 171 | 62,910 | 36,048 |
| **331** | **133** | **72,065** | **26,893** |

The source conversation links the selected split to two purported prime sums, 71,963 and 26,893. Only the latter reproduces from this archive's nine-page ciphertext transcription. The reporter's exact 464-word input list was not supplied, so the 102-point difference is an **unresolved source discrepancy**; it does not prove the original calculation was impossible on another transcription.

The pointer arithmetic is less selective than it first looks: for any cut after forward word *k* in a 464-word list, reverse word *(464 − k)* is automatically the next forward word. The audit therefore checks every adjacent STUDY HERE occurrence and every one of the 463 possible cuts. Thirteen cuts have prime GP sums on both sides, while the selected 331 cut has a prime on only the final side. These are descriptive counts, **not a probability**: the positions, phrase and number links were discussed after the solved text was available.

The [plan](experiments/records/study-here-bidirectional-pointer/plan.json) fixes the four-section word order and counting rule. The [result](experiments/records/study-here-bidirectional-pointer/results.json) records input hashes, all five phrase locations and the prime-cut count. Reproduce it from the repository root with `python experiments/records/study-here-bidirectional-pointer/run.py --check`; the underlying independent word/token audit is `python scripts/audit_464_pointer.py --check`. This tests the reported **LP1 pointer**, not whether it specifies an LP2 decryption.
