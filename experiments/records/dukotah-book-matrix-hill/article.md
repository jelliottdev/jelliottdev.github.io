# Number panels as Hill-cipher keys

Could the numerical panels associated with Liber Primus act directly as block-cipher matrices? A [pinned Campaign VII program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/hill5_magic.py) supplied six 5×5 or 4×4 candidate matrices. It multiplied each consecutive block of rune indices by the matrix, its transpose, its inverse or the inverse transpose, modulo 29.

For example, LP2-15 starts with **F U L M**, rune indices **0, 1, 20, 19**. The source’s 4×4 matrix turns that block into **N E H O** (indices **9, 18, 8, 3**). The same operation then continues on every four-rune block; it cannot pick a different rule for an awkward word.

**Finding:** the original **1,344 page-or-book candidates** reproduce the archived source result. None reaches its declared English-score flag of **−5.0**; the best is **−6.873**. A complete **85-rune known reading** *does* recover exactly when enciphered and then decoded under every invertible tested operation, and scores above the flag. This test does not reveal a readable LP2 page under those fixed operators.

![The six source matrices and one corrected-grid input all remain below the source's English score flag.](experiments/records/dukotah-book-matrix-hill/comparison.svg)

There is a material input error in the source’s 4×4 candidate: its last cell is **820**, while the [LP2-15 number panel](#/reader/lp2-15) reads **1820**. The source's 4×4 rows also do not sum to one constant, so that panel should not be described as a 4×4 magic square. We reran its four operations with *only* that cell corrected. None of the **224** additional outputs reaches −5.0; the best is **−6.907**. The source’s separate “phi” variant was left as its own literal array because its cell-generation rule is not supplied. Correcting one matrix does not validate or revise the other five.

The source's winning label `p54` refers to its 55th **rune-bearing** segment, which maps to **LP2-55**: rune-free LP2-50 is absent from its page list. We checked all 55 source rune arrays against the corresponding page records; they match exactly. This page mapping matters when inspecting the winning output.

The source **drops an incomplete final block** rather than padding manuscript pages. Across the 55 page-local runs, a 4×4 operation omits 80 trailing runes on 43 pages; a 5×5 operation omits 116 on 48 pages. The one joined stream omits zero or one, respectively. Page-local scores therefore do not include every rune. For the positive controls only, we zero-padded the full 85-rune known reading before enciphering, then removed that declared padding after decoding and required all 85 original runes. The [initial control receipt](experiments/records/dukotah-book-matrix-hill/initial-control-receipt.json) preserves the earlier 4×4 plant that stopped after 84 runes; the full-length plant is a later control amendment, not a pre-outcome result.

The whole search was repeated on **199** shared pagewise rune shuffles. The original 24-operation search's best score was equaled or exceeded in **146** shuffles; the corrected-cell four-operation search's best score was equaled or exceeded in **69**. Each trial shuffles every page once and reuses those shuffled pages across all operations, preserving the dependence in the selected maximum. These are conditional comparisons of rune order, not probabilities that a Hill cipher generated LP2.

This replay covers page-local block origin zero on LP2-00–55 excluding runeless LP2-50, plus one joined rune stream. An incomplete final block is dropped. The tested matrices are fixed inputs, not an exhaustive search over 4×4 and 5×5 Hill keys. Other origins, block directions, offsets, affine constants, key schedules, plaintext languages and interpretations of the panels remain open. The earlier [complete small-block feasibility test](#/experiments/direct-hill-key-feasibility) asks a different question about unknown 2×2 and 3×3 keys at page starts.

Download the experiment files and run these commands from the extracted repository layout:

```text
python experiments/records/dukotah-book-matrix-hill/run.py --check
python experiments/records/dukotah-book-matrix-hill/check.py
python experiments/records/dukotah-book-matrix-hill/plot.py --check
```

The first command replays the source in a temporary copy and recalculates all results, leaving the archived source output untouched. The independent checker reconstructs the matrix products, inverses, scores and page mapping without importing the producer. Both commands use the bundled source transcription and quadgram model; the manuscript-cell check and known-reading plant also use the site's page record and reading CSV. The [first-frozen plan](experiments/records/dukotah-book-matrix-hill/plan-original.json) is preserved beside the amended reproduction plan, so the later full-length plant can be distinguished from the fixed manuscript search.
