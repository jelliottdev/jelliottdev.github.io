# Does the 1,894-rune count give a useful alignment?

**Result.** No unusual alignment appears under four fixed arithmetic readings. The best printed-order output has an index of coincidence of **0.034549**. Of the 1,893 nonzero circular shifts used as controls, **1,410 score at least as high** after the same four-way choice. This tests a proposed use of the equal length, not whether the section-count equality itself is correct.

![The observed pairing lies within the range of shifted pairings; 1,410 of 1,893 shifts score at least as high.](experiments/records/section-1894-pairing/comparison.svg)

The published [section-count sheet](#/wiki/section-rune-counts) gives **1,894** runes on each side: Koan 1, Loss of Divinity, Koan 2 and Instruction after removing every F; and the Möbius section after its nine-rune heading with F retained. The first stream uses solved LP1 page *runes*, not the English reading. We rebuilt both streams directly from the archived page transcriptions, retaining their printed order and the explicit section breaks on LP1-16 and LP2-15.

For each aligned pair of rune indices `A` and `B`, the test forms `(B + A) mod 29` or `(B − A) mod 29`, with `B` either forward or reversed. Each complete output receives a whole-stream equal-rune-pair score, reported as index of coincidence (IoC); the **highest of the four** is the chosen score. We repeat that whole selection for every circular shift of `B`, so the control includes the choice among the four operations.

| Printed-order operation | Equal-rune pairs | IoC |
| --- | ---: | ---: |
| Add | 123,206 | 0.034364 |
| Subtract | 123,468 | 0.034437 |
| Reverse, add | **123,870** | **0.034549** |
| Reverse, subtract | 123,266 | 0.034381 |

The observed best score is **below the median shifted best score** of 124,096. Its rank is ordinary under this narrow comparison; the count match alone does not choose an operation or recover readable text. The [full result](experiments/records/section-1894-pairing/results.json) saves all 1,894 best-of-four scores, and the [plan](experiments/records/section-1894-pairing/plan.json) fixes the operations and exclusions.

Run `python experiments/records/section-1894-pairing/run.py --check` and `python experiments/records/section-1894-pairing/check.py` from the repository root. The second program independently rebuilds the section streams and checks the observed variants and selected shifts. This control conditions on a previously noticed equality and one score. It does not cover every section pairing, every cipher operation, or a full language-based reading test.
