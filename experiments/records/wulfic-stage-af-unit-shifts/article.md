# Could a restarted key also shift at every boundary?

**The tested shifted-restart model still does not fit LP2.** Giving each page, line or other unit its own additive shift removes the simple rune-for-rune comparison used in the [basic restart test](#/experiments/wulfic-stage-ab-reset-alphabets). It does not remove a second property: subtract two ciphertext runes *within the same unit*, and that unit's shift cancels. If the underlying position key restarts, equal plaintext differences at the same two positions still produce equal ciphertext differences across units.

![Five shifted-restart comparisons: LP2 near the random expectation, planted controls to the right.](experiments/records/wulfic-stage-af-unit-shifts/comparison.svg)

Each blue point is LP2's full difference-match count divided by the random-rune expectation for that boundary. Gray is the conservative lower bound from planted shifted-restart encryptions. **The horizontal scale is zoomed from 0.98 to 1.08** to make the modest but consistent separation visible; it does not start at zero. None of these points is decoded text.

## What was tested

This is a byte-for-byte replay of [Wulfic's Stage AF program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_af.py) at its pinned revision. The model uses one shared key value at each position after a restart and one extra shift for each unit. It covers both additive and Beaufort directions in planted controls. For every section, paragraph, clause, line and page boundary, the statistic compares ciphertext differences between positions **2–300 runes apart within that same unit**. The complete input is **12,956 runes across 55 rune-bearing LP2 pages**.

The source tested **200 flat-rune nulls** and **100 planted encryptions for each of two plaintext sources**, Emerson essays and solved LP readings. Its anti-doublet rule was applied to controls. A test could be called excluded only where both planted sources separated from the null and LP2 fell below both predeclared five-standard-deviation lower bounds. The frozen [plan](experiments/records/wulfic-stage-af-unit-shifts/plan.json) records the exact rule and source hashes.

The page-reset case is illustrative: LP2 had **1,207,810** matching within-page differences; random controls averaged **1,208,036**. The weaker planted lower bound was **1,242,113**. The same comparison held at the other four boundaries, so the source marks all five cells **excluded under this model**. Our full source run reproduced its [results](experiments/records/wulfic-stage-af-unit-shifts/source-stage_af_results.tsv) and [controls](experiments/records/wulfic-stage-af-unit-shifts/source-stage_af_controls.tsv) byte-for-byte.

This does not rule out every resetting key. It tests a **shared position key plus one constant shift per unit**, using the source's plaintext examples and doublet treatment. Position-dependent shifts inside a unit, nonlinear feedback, a different plaintext distribution or a different boundary rule can erase this particular difference invariant. Even if the invariant were present, it would not alone identify a decryption key.

## Reproduce

Run `python experiments/records/wulfic-stage-af-unit-shifts/run.py --check` and `python experiments/records/wulfic-stage-af-unit-shifts/check.py` from the repository root with NumPy installed. The [independent checker](experiments/records/wulfic-stage-af-unit-shifts/check.py) rebuilds all five partitions from Liberpedia's page transcriptions and counts the difference collisions with a separate pure-Python method. It also encrypts a planted three-unit example in both additive and Beaufort forms and verifies that each unit's shift cancels.

For the full upstream Monte Carlo replay, clone the [pinned source repository](https://github.com/Wulfic/Cicada3301-Liber_Primus), check out `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`, install NumPy, and run `python experiments/records/wulfic-stage-af-unit-shifts/replay_source.py --source-dir PATH_TO_CLONE`. The wrapper hashes source code and inputs, runs in a temporary output directory, and compares both resulting tables byte-for-byte.
