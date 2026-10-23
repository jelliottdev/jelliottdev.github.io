# Replaying the LP2-15–22 Roman matrix proposal

The two supplied guides construct digit grids from Gematria Primus (GP) prime values, map the printed [LP2-15](#/page/lp2-15) number panel into those grids, then connect seven transposed panel entries to Roman numerals and the word **HALFMAN**. We reproduced the stated counts and contacts against Liberpedia’s archived rune text. This is a replay of a **conditional construction**: it has not decrypted LP2-15–22.

![A compact trace from the reported digit grids through the Roman initials, with the local selection check](experiments/records/cc-roman-matrix-replay/trace.svg)

| Check | Reproduced result | What it establishes |
| --- | --- | --- |
| LP2-15 body, excluding nine-rune header | 150 runes → **289 digits = 17²** | The square fit needs the eleven red body runes. |
| LP2-16–22, all runes | 1,744 runes → **3,481 digits = 59²** | A second exact square fit under the stated concatenation. |
| Alternating rune-start/rune-end at 16 registered contacts | **12/16** on 17²; **16/16** on 59² | A real property of the stated registration and streams. The contacts are dependent and the registration was selected during investigation. |
| Transposed panel, positions 5–11, Roman initials | `L X L L L X V` → `L L L L X X V` in direct HALFMAN order | Values sum to **225** and end descending. Ordering does not change the sum. |
| Eight orientations × ten seven-position windows | **2/80** show both 225 and descending output | Both hits use the **same seven panel values**. They are not two independent confirmations. |

## Follow one result

The position map sends printed coordinate 1→2, 2→3, 3→*N*−1, and 4→*N*. On each center-out digit spiral, registered positions 9, 10 and 11 straddle the final inner-square boundary. On the 17² grid, digits 225–226 are the two digits of **X = 47**, followed by the beginning of **NG = 79** at 227. On the 59² grid, digits 3249–3250 are **J = 37**, followed by **Y = 103** at 3251. This reproduces the reported beginning → end → beginning pattern in both streams. The inner-square addresses are fixed by the grid sizes; the rune-boundary coincidence is an additional observation under the chosen registration.

For the number trial, transposed positions 5–11 hold **3152, 3222, 3258, 3278, 3288, 4516, 1206**. Their last two digits are 52, 22, 58, 78, 88, 16 and 06. The first symbols of the corresponding Roman numerals are L, X, L, L, L, X and V. These individual symbol values add to **225**; the conventional Roman numeral for 225 is **CCXXV**, so `LLLLXXV` is an additive symbol list, not standard notation.

The [printed](#/wiki/lp2-15-panel) positions 5–11 have zero-based Fibonacci prime indices **5, 8, 13, 21, 34, 55, 89**, which also sum to 225. That arithmetic was already present in the selected panel window; the HALFMAN permutation only rearranges the Roman-symbol list. The proposed words FORK, DEDUCED, ROMANA, TO and HALFMAN come from an alphabet reconstructed from those same proposed word pairs. Fitting them does not independently validate the selector.

## How sensitive is the Roman result?

Keeping the seven-position window at 5–11 but using the printed panel yields **230**, not 225. Moving the transposed selection to positions 6–12 yields **180**. Inverting the HALFMAN order leaves the transposed 5–11 sum at 225 but makes the values **not descending**. Our fixed, local scan checks all eight square symmetries and all ten possible consecutive seven-position windows. Two of the 80 combinations satisfy both conditions, but they select exactly the same seven-number sequence under differently labeled orientations. The scan documents nearby choices; it cannot supply a p-value for the broader search that led to the proposal, which also includes word readings, digit extraction, Roman symbol choice, rank direction and coordinate registration.

The 16/16 larger-grid boundary result is worth preserving as a structural observation. It is not sixteen independent predictions: contacts can share a rune, and the same chosen representation and registration generate every contact. A cipher test would need a rule selected **before** inspecting a fresh passage that predicts where to read, what to emit and how to continue past position 11. The PDFs expressly leave that step open.

## Reproduce

From the repository root, with Python 3 and no external packages:

```text
python experiments/records/cc-roman-matrix-replay/run.py --check
```

The [plan](experiments/records/cc-roman-matrix-replay/plan.json) fixes the source and choices; the [results](experiments/records/cc-roman-matrix-replay/results.json) include every registered address, its rune span, all 80 local Roman trials and input hashes. The [source-intake note](research/source-intake/cc-stage-replay-2026-10-22.md) records the two PDF hashes and scope.
