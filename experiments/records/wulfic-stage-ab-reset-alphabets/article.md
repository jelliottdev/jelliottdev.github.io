# Do page and line starts reset an alphabet?

**This particular restart model does not match the unsolved manuscript.** At a fixed position after each restart, the model uses the same substitution alphabet every time. A repeated plaintext rune at that position should therefore produce a repeated ciphertext rune. The five proposed restart points—section, paragraph, clause, line and page—were all checked. LP2's same-position repeats stayed close to a random-rune baseline and below the conservative range of planted examples.

![Five restart-boundary comparisons: LP2 near the random-rune expectation, planted examples higher.](experiments/records/wulfic-stage-ab-reset-alphabets/comparison.svg)

The blue bars are LP2. The gray bars begin at the **lower bound** of simulated manuscripts deliberately encrypted with an alphabet that restarts at the named boundary. Ratios use a separate random-rune expectation for each boundary, so a value of 1 means “about as many matches as random output.” The bars do not represent decoded text.

## What was tested

This is a replay of [Wulfic's Stage AB source program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ab.py), not a new proposed decryption. It takes all **12,956 runes on the 55 rune-bearing LP2-00–55 pages**. For each boundary type, it groups runes by their position from the start of that unit. It then counts pairs of units that carry the same ciphertext rune at the same position. Words that wrap across a line or page do not create a new clause or paragraph.

The original run compared each count with **1,000 random-rune controls** using the source's measured anti-doublet rule, then tested detection power with **200 planted restart encryptions from each of two plaintext sources**: Emerson essays and known LP readings. The source's lower bound is five standard deviations below the mean of log(count + 1), transformed back to counts. The frozen inputs, random seed **3301**, threshold and source revision are in the [plan](experiments/records/wulfic-stage-ab-reset-alphabets/plan.json).

| Restart point | LP2 matches | Random mean | Weaker planted lower bound |
| --- | ---: | ---: | ---: |
| Section | 1,125 | 1,145 | 1,755 |
| Paragraph | 1,484 | 1,525 | 2,365 |
| Clause | 20,028 | 19,874 | 32,271 |
| Line | 126,508 | 125,457 | 203,912 |
| Page | 10,751 | 10,726 | 17,307 |

For all five rows, even the lowest of the planted control results is above the highest random control. LP2 is below the planted lower bound in both plaintext sources. The source therefore marks each row **excluded within this model**. Our full run reproduced the upstream [result table](experiments/records/wulfic-stage-ab-reset-alphabets/source-stage_ab_results.tsv) and [control table](experiments/records/wulfic-stage-ab-reset-alphabets/source-stage_ab_controls.tsv) byte-for-byte.

The finding does **not** reject every cipher that restarts on a page or line. It concerns a shared, position-dependent substitution alphabet, the source's plaintext examples and its post-encryption anti-doublet process. A changing key, feedback, distinct alphabet at each unit, different plaintext distribution or another preprocessing rule can break this invariant. It also does not tell us what cipher LP2 uses.

## Reproduce

Download this experiment and run `python experiments/records/wulfic-stage-ab-reset-alphabets/run.py --check`, then `python experiments/records/wulfic-stage-ab-reset-alphabets/check.py`. The [independent checker](experiments/records/wulfic-stage-ab-reset-alphabets/check.py) rebuilds the complete rune stream and all five boundary partitions from Liberpedia's page JSON, matches the [frozen source-derived layout](experiments/records/wulfic-stage-ab-reset-alphabets/layout.json), and recalculates the observed statistic and analytic random expectation. It also checks a planted, fixed-position substitution example.

To rerun all 1,000 null and 2 × 200 planted trials under the **original source code**, clone the [source repository](https://github.com/Wulfic/Cicada3301-Liber_Primus), check out commit `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`, install NumPy and run `python experiments/records/wulfic-stage-ab-reset-alphabets/replay_source.py --source-dir PATH_TO_CLONE`. The wrapper verifies the source revision and input hashes, writes into a temporary directory, and requires byte-identical output tables. The manuscript is not reinterpreted or rescored in that replay.
