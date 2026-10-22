# Does the 256-cell grid layout change the missing primes?

Yes. In the manuscript’s **32 × 8** arrangement, the four-cell search misses 1033, 2213 and 3301. Reshape the *same ordered cells* into **16 × 16**, and all three appear twice. Restrict those 16 × 16 paths to their own **8 × 8 quadrant**, and the three still appear. The original missing set therefore depends on the grid layout.

![Observed number of missing values for each layout, with central ranges from shuffled digits.](experiments/records/grid-alternative-layouts/layouts.svg)

## Fixed search rule

Take the first digit of each of the 256 two-character tokens on LP2-49–51. Read four adjacent cells in any of eight straight directions, without wrapping or turns. Reject a path containing 4; allow leading zeroes; retain the resulting decimal number only if it is prime. There are **49** possible four-digit spellings from 0–3 that pass this test. The [original-layout recount](#/experiments/grid-prime-paths) defines the baseline.

The 16 × 16 test changes only where row breaks fall. Its quadrant version also forbids paths crossing an 8 × 8 block boundary. No cells are reordered within the underlying 256-token sequence.

| Layout | Directed paths | Prime occurrences | Distinct primes | Missing values |
| --- | ---: | ---: | ---: | --- |
| Original 32 × 8 | 1,364 | 191 | 46 | 1033, 2213, 3301 |
| Reshaped 16 × 16 | 1,508 | 206 | 49 | None |
| Four fixed 8 × 8 blocks | 1,040 | 148 | 45 | 2003, 2111, 3023, 3203 |

The three named values each have **two** directed hits in the 16 × 16 layout. In the quadrant search, 1033 and 3301 have two each and 2213 has one. Opposite reading directions can share cells, so these are occurrences, not necessarily independent locations.

## Control and limit

We shuffled the 256 first digits **3,000** times, preserving their overall frequencies, and repeated each fixed layout. Missing-value counts in the observed grids fall within the central 95% ranges of these shuffles: 0–4 for 32 × 8, 0–3 for 16 × 16, and 0–7 for the quadrant layout. The figure shows those ranges, not a probability that the manuscript was made by shuffling.

These layouts and the names 1033, 2213 and 3301 were considered after the original pattern was noticed. The controls cannot turn their post-hoc selection into a prospective test. This experiment does **not** examine suffix letters, the five-dot artwork, alternate paths, or an LP2 decoding rule. It shows that an absence claimed for one geometry is not stable under two simple, explicitly stated alternatives.

## Reproduce

From the repository root, with Python 3.12 and no extra packages:

```text
python experiments/records/grid-alternative-layouts/run.py --check
python experiments/records/grid-alternative-layouts/check.py
```

The first command rebuilds the table, controls and figure. The independent checker enumerates endpoint pairs to verify the observed counts. [Results and shuffle histogram](experiments/records/grid-alternative-layouts/results.json) give the exact values. The [source account](https://github.com/o3rynn/cicada-faw) motivated checking these layouts; the statistics and controls here are our scoped reproduction.
