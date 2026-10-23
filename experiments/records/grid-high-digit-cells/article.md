# The grid's 4-prefix cells

**Finding:** Seventeen of the 256 pairs on LP2-49–51 begin with `4`. Their suffixes are restricted, but that restriction follows from a byte-sized base-60 reading: `4 × 60 + digit` cannot exceed 255, so the suffix digit must be 0–15 (`0–9`, `A–F`). This does not make the cells a separate cipher channel. Their positions are less evenly spread than a simple random-placement control, which is an observation worth preserving without assigning it a decoding role.

![Map of the seventeen 4-prefix cells across four consecutive eight-row blocks.](experiments/records/grid-high-digit-cells/cells.svg)

The suffixes, in manuscript order, are `97DEF756B98A80EB9`: **11 distinct symbols**, not five as stated in the source account. The five *missing* hexadecimal symbols are `1`, `2`, `3`, `4` and `C`. These counts use the archived [grid transcription](#/wiki/alphanumeric-grids); its five known disagreements with another quoted transcription do not affect these `4`-prefix cells.

| Fixed measurement | Result |
| --- | ---: |
| `4`-prefix cells | 17 of 256 |
| Cells in four consecutive 8×8 blocks | 4, 2, 9, 2 |
| Horizontally or vertically touching pairs | 7 |

For a limited placement check, the script chose 17 of 256 positions uniformly in 20,000 seeded trials. **43 trials** had at least seven touching pairs; **804** had a block containing at least nine marked cells. A second control preserved the observed count in *each row* and randomized only columns: **464 of 20,000** trials had at least seven touching pairs. These are descriptive reference frequencies, not a probability that Cicada engineered a second layer. The positional statistics were selected after seeing the table, and a uniform-position model ignores other structure in its construction.

Nothing here specifies what to read from the 17 cells, in what order, or how to test that output on another page. A separate-channel proposal would need those rules before examining its result. The [base-59/base-60 record](#/experiments/grid-radix-reconciliation) checks the broader digit-alphabet question.

## Reproduce

From the repository root, run `python experiments/records/grid-high-digit-cells/run.py --check` and `python experiments/records/grid-high-digit-cells/check.py`. Both use only Python's standard library; the second independently recounts the deterministic cell and adjacency measures from the coordinate-bearing export. The [plan](experiments/records/grid-high-digit-cells/plan.json) fixes the two placement controls and seed; [results](experiments/records/grid-high-digit-cells/results.json) include their full histograms. The [pinned source account](https://github.com/o3rynn/cicada-faw/tree/72f92e7ac8acf9b2e660e23d654107652cb00fb0) describes the proposed distinct `d=4` group.
