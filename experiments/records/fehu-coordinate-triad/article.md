# A 59-Fehu coordinate triad in LP2

**Finding.** A reported construction is arithmetically reproducible on Liber Primus part two (LP2). Of 350 eligible starting Fehu runes, one start—**F182**—produces the ordered sums **3001, 2819, 2579** under the source's fixed three-window rule. All 177 coordinate labels in the three supplied streams also agree with the archived rune data. This is a numerical match, not a decryption or a probability that Cicada intended the construction.

The proposal treats every F/Fehu rune as a position marker. First concatenate LP2-00 through LP2-57 in page order, keeping the 29 manuscript runes and dropping punctuation. Number the resulting Fehus F1, F2, and so on. This produces 13,136 runes and 466 Fehus. The count is **LP2-only**: adding LP1 changes every later Fehu number. F182 occurs at zero-based rune index 4,949 in this stream.

For each chosen Fehu, subtract an origin Fehu's rune index. Put that distance on a grid 29 columns wide: its remainder after division by 29 is X, and the quotient modulo 29 is Y. Read X or Y as a zero-based Gematria Primus rune index and add the corresponding prime values. For example, F182 has offset zero from itself, so its X value is 0, the F rune worth 2. F183 is 60 runes later: `60 mod 29 = 2`, the TH rune worth 5. The source writes V for the rune indexed 1; this archive labels it U. The indices and prime values are the same.

| Window | Coordinate and origin | Recomputed GP sum | Reported target |
| --- | --- | ---: | ---: |
| F182–F240 | X, origin F182 | 3001 | 3001 |
| F211–F269 | Y, origin F182 | 2819 | 2819 |
| F240–F298 | X, origin F240 | 2579 | 2579 |

The starts are 29 Fehus apart. The middle window crosses the shared F240 seam; the last window resets its origin there. These details matter. Using F240 as the middle origin or keeping F182 as the last origin asks a different question. The archived [plan](experiments/records/fehu-coordinate-triad/plan.json) fixes all three choices before the replay. The [results](experiments/records/fehu-coordinate-triad/results.json) retain the three sums at every eligible start, not just the match.

![Three stacked line plots show the coordinate-prime sums across all 350 eligible starts. Dashed horizontal lines mark the three reported targets and a vertical line marks F182.](experiments/records/fehu-coordinate-triad/coordinate-scan.svg)

Only F182 yields all three exact targets in order among the 350 complete start positions **under this one rule**. That does not make the chance of the reported finding 1 in 350. The source describes an exploratory sequence: a 59-Fehu window, a 29-column grid, X and Y choices, target message segments with F included or removed, and an origin reset were selected or refined while looking at the data. The number of tried alternatives is unknown. Many such choices can create a unique exact hit, especially when large prime sums are used as targets. We have not run a selection-aware maximum over that wider search family or checked a predicted key or plaintext on untouched LP2 material.

The three target numbers are presented in the supplied discussion as adjusted sums from a 2016 message. This record reproduces the **LP2-side coordinate arithmetic** and checks the source's supplied coordinate streams; it does not independently establish that those message adjustments were specified in advance. The reported 2017 value 2131 has no placement in this triad. Nor does a match explain how coordinate values would decode neighboring runes.

## Reproduce the bounded check

Python 3.12 and its standard library suffice, offline:

```text
python experiments/records/fehu-coordinate-triad/run.py --check
python experiments/records/fehu-coordinate-triad/check.py
python experiments/records/fehu-coordinate-triad/plot.py --check
```

The producer verifies the three full label streams from the supplied discussion and enumerates all 350 starts. The separate checker recounts Fehus from each stored page line, recalculates every start with a different loop, and checks the one exact ordered match. The plan and report identify the local source extract by SHA-256; the private discussion transcript is not a retrievable public citation. See the [F-interrupter guide](#/wiki/interruptions), [prime-sum guide](#/wiki/prime-sums), and [search-space guide](#/wiki/search-space) before treating a numerically precise fit as a cipher rule.
