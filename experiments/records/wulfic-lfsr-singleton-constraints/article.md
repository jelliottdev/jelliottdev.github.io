# Can single-rune words pin down an LFSR key?

An [LFSR](#/wiki/method-seeded-generators?section=lfsr) generates a key from a short memory of earlier values. Here it remembers one to five rune indices and calculates each next value modulo 29. The test assumes that every visible one-rune word in the unknown plaintext is **I** or **A**.

**Finding.** With one or two values of memory, no tested setting fits all the one-rune words on any of the three pages. With five, LP2-21 admits about **5.8 million** fitting parameter settings and LP2-24 about **27,400**. LP2-28 admits **four**, all under the Beaufort direction. A fit means only that those few positions read I or A; none is an established reading of the page.

![Number of LFSR parameter settings satisfying every visible one-rune word as I or A, by page and key memory length.](experiments/records/wulfic-lfsr-singleton-constraints/fits.svg)

The source's historical labels P28, P24 and P21 refer to **LP2-28, LP2-24 and LP2-21**. In the pinned repository's current global page folders, those are scans **45, 41 and 38**. We checked the rune streams and the precise positions of the 12, 9 and 7 one-rune words against the unchanged source parser before scanning. Using today's `page_28` folder would instead test LP2-11.

| Page | One-rune words | Complete fits at L3 | L4 | L5 |
| --- | ---: | ---: | ---: | ---: |
| LP2-28 | 12 | 0 | 0 | **4** |
| LP2-24 | 9 | 0 | 24 | **27,424** |
| LP2-21 | 7 | 6 | 6,846 | **5,808,457** |

These counts combine the source's subtraction and Beaufort directions. Its addition direction gives the **same decoded streams** as subtraction with every initial key value negated, so it is reported in the result file but not counted twice in the table. At L1 and L2, none of the three pages has a complete fit. Every L5 row includes all **20,511,149** ordered feedback tuples, including zero coefficients.

The four LP2-28 candidates have normalized full-page indices of coincidence **0.978–1.142**, below the source's `>1.3` shortcut. That observation is descriptive: we did not calibrate the source's other dictionary shortcut over the entire selected grid, and neither shortcut would establish a decryption by itself. The [result file](experiments/records/wulfic-lfsr-singleton-constraints/results.json) gives each of those four full-page decode hashes, key parameters, and exact singleton values. It also preserves example decodes for the larger rows.

## What the calculation covers

For state length L from **1 through 5**, the source defines each next key value as a linear combination of the previous L key values modulo 29. Its solver tries all tap tuples and all I/A assignments for the first L one-rune words, solves for the starting state, then checks every remaining one-rune word. We reproduced that **first-L invertible** procedure in all three directions. Planted streams recovered their exact taps and starting states for every length and direction. An independent checker recalculates every L1/L2 result, the first 100 tap tuples at L3–L5, every published full-page example, and the pinned input positions. It also exhausts small GF(3) and GF(5) tap/state spaces against a direct recurrence oracle and tests nonconsecutive singleton positions in GF(29). These checker controls were completed after the manuscript scan; the small-field oracle had been specified in the frozen plan.

This is a test of a **specific English singleton crib and source search rule**. If one-rune words use other plaintext symbols, the state advances across pages, the key skips, or the first-L basis is singular, these counts do not decide the model. In particular, millions of L5 fits on the page with only seven one-rune words show why satisfying a small crib is not evidence of a solution. A candidate needs a rule fixed in advance that predicts substantial text outside the singleton positions.

To repeat the saved-output checks, run:

```text
python experiments/records/wulfic-lfsr-singleton-constraints/run.py --check
```

The full four-minute sweep needs a C++17 `g++` compiler:

```text
python experiments/records/wulfic-lfsr-singleton-constraints/run.py
```

The [plan](experiments/records/wulfic-lfsr-singleton-constraints/plan.json) fixes the bounds and assumptions. The [input ledger](experiments/records/wulfic-lfsr-singleton-constraints/inputs.json) pins the page text and one-rune positions. The [pinned source script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/lfsr_gf29_solver.py) defines the historical proposal; its archived execution and old optimizer output are not treated as verified results.
