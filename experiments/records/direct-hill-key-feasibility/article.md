# Direct Hill keys at LP2 page starts

**Question.** Can a single invertible linear block key over the 29-rune alphabet turn the first twelve runes of an unsolved LP2 page into a fixed known-reading opening?

**Result.** No such key fits any of the **495 page-and-opening pairs** for two-rune blocks or the **495 pairs** for three-rune blocks. This is a complete key-feasibility check for the stated block rule: it does not sample a few matrices or assume a convenient key.

![One matrix must preserve the relationships among every block.](experiments/records/direct-hill-key-feasibility/block-rule.svg)

## What the test means

Each rune has its usual Gematria Primus index from 0 to 28. We divide the first twelve runes into consecutive blocks of two or three, starting at the first rune of each page. For one proposed opening, the same unknown matrix **D** must satisfy **P = D·C (mod 29)** for *every* corresponding ciphertext and plaintext block. A later block cannot be handled with a different key. The nine target openings were fixed in the earlier known-readings test.

We do not need to try the enormous set of possible keys. First choose independent ciphertext blocks. Their proposed plaintext blocks determine what D must do on that span. Every other ciphertext block is a combination of those basis blocks, so its target must obey the same combination. Finally the target basis must remain independent; otherwise D cannot be invertible. If the ciphertext span is incomplete, the check counts every possible invertible extension instead of falsely rejecting it. For rank *r* in dimension *n*, that count is the product of **29ⁿ − 29ʲ** for **j = r, …, n−1**.

Here all 55 tested page starts have full ciphertext rank in both dimensions. Their first independent blocks therefore determine a unique possible matrix. In every one of the 990 comparisons, a remaining block disagrees with that matrix. None of the nine opening readings is obtained under this exact direct rule.

## Limits and reproduction

The test covers **LP2-00–55 except runeless LP2-50**, page-local origin zero, the first twelve runes including headings, dimensions two and three, and nine fixed 12-rune openings. It does not test other plaintexts, later positions, block offsets or directions, an affine constant, padding, transposition, or a key that changes between blocks. It does not test the LP2 number square as a key schedule.

Download the experiment files and run `python experiments/records/direct-hill-key-feasibility/run.py --check` followed by `python experiments/records/direct-hill-key-feasibility/check.py` from the repository root. The second program reads the independent page JSON, uses a separate stacked-rank criterion for all 990 cases, and checks small-field predictions against **all** invertible 2×2 and 3×3 matrices over F₂ and F₃. Those controls include full-rank, rank-deficient, zero-input, and inconsistent cases. The per-case result file records the page, opening, rank, and number of compatible keys.
