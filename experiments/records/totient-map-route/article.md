## What was tested

The proposed 27 × 27 reading can be reproduced **when its selected cells and key nodes are supplied**. This experiment checks that arithmetic, the map itself, and the additional rules for predicting properties of the next block. It does not find the route from the manuscript without those selections.

The source is pinned to commit `d5eed3f10428372c7202ceebc65cc3bdead0819d`. Later edits to that repository are outside this result. The downloadable input records the coordinates, keys, source-file hashes and proposed output rune indices. No language model or language scorer chooses words in this replay.

## Results at a glance

| Check | Result | What it establishes |
| --- | --- | --- |
| Map compared with archived LP2-00–02 | 729 of 729 cells agree | The selected matrix uses our transcription in page order |
| Main reading | 17 blocks, 61 rune subtractions reproduce | Correct arithmetic for supplied choices |
| Alternative SOON block | 4 further subtractions reproduce | A second supplied route produces the same word |
| Next-key signature | 16 of 16 transitions match | Fit to the recorded route |
| Next axis and boundary role | Each matches 16 of 16 | Further fit to the same route, not independent discoveries |
| Ciphertext coverage | 54 distinct cells of 729, about 7.4% | The proposed reading is a selection, with reused cells |
| Same SOON key from three nodes | Horizontal / diagonal / diagonal | Key equality does not settle the node choice |

**Outcome: inconclusive as a decryption claim.** Successful arithmetic is a real result. The supplied rules do not yet uniquely select and read the full matrix, and this experiment does not establish whether the proposed passage was intended.

[Open the full-size coverage map](exports/figures/totient-map-coverage.svg) · [Open the node-choice diagram](exports/figures/totient-map-node-choice.svg)

## How the map is made

Read [LP2-00](#/page/lp2-00), [LP2-01](#/page/lp2-01) and [LP2-02](#/page/lp2-02) in that order. Keep every rune, including the heading, remove punctuation and spacing, and fill rows of 27 from left to right. Coordinates start at (1,1). This gives exactly 729 cells; the repository's displayed map agrees cell by cell. It is a rearrangement of the text, not the original page layout.

The coverage figure highlights only ciphertext cells used in the primary route. Keys and navigation landmarks can use other cells. There are 61 output positions but only 54 distinct ciphertext cells because several are read more than once. Reuse is not automatically an error in a geometric cipher; it needs an explicit rule, just as skipping cells does.

For the functions themselves, see [Euler’s totient](#/wiki/totient) and [the Möbius function](#/wiki/mobius-function).

## A complete arithmetic example: WEATHER

The node at row 14, columns 4–6 is X–OE–X, with indices 14,22,14. Replace the middle index by its totient: φ(22)=10, giving X–I–X. Apply μ(φ(k)) to each derived key index. The signature is (1,0,1), whose sum modulo 3 is 2. Rotate the key left twice to get X–X–I and repeat it.

| Cipher cell | Cipher index | Key index | Difference modulo 29 | Output |
| --- | --- | --- | --- | --- |
| (14,14) | NG = 21 | X = 14 | 7 | W |
| (14,15) | P = 13 | X = 14 | 28 | EA |
| (14,16) | EO = 12 | I = 10 | 2 | TH |
| (14,17) | O = 3 | X = 14 | 18 | E |
| (14,18) | E = 18 | X = 14 | 4 | R |

Five output runes spell WEATHER. This calculation does not itself explain why those five cells are chosen, why the block stops there, or which block follows. The opening block also crosses a row boundary, whereas later selections include vertical and diagonal segments. TURNS uses its three node indices directly rather than transforming the center. Those choices are preserved in the replay instead of silently replacing them with a uniform rule.

The output trace retains rune tokens such as TH and EA. Spaces and punctuation in the proposed English reading are editorial interpretations, not separate decoded symbols.

## What the transition rules add

The source provides more than word examples. It predicts a next-key signature using Möbius values of current block coordinates. It switches between direct and half-turned positions at cumulative phase totals 7 and 14. A quarter-turn calculation updates the outer signature state. A separate formula involving the current beginning, end and original node center predicts horizontal, vertical or diagonal; another predicts whether the next block's leftmost cell is its beginning or end.

We recomputed all 16 primary transitions, treating OF and THE separately and using the primary SOON route. All three checks match. The starting state, block boundaries, node centers and phase thresholds are inputs. The source states that the thresholds were identified from this route. Consequently, **16 matches are an in-sample fit, not 16 held-out predictions**. The signature, axis and boundary checks also share inputs and must not be multiplied as independent probabilities.

### How many keys share a signature?

A signature constrains a key without identifying its runes. For example, (0,0,0) is shared by 4,096 ordered triples of positive rune indices; (1,0,1) by 1,296. These counts enumerate indices 1–28 only. They exclude F=0, for which the standard positive-integer totient is not defined here. They are not counts of reachable nodes: geometric restrictions can reduce the candidates considerably.

For each derived key index k, compute μ(φ(k)). Among indices 1–28, 16 give zero, 3 give −1, and 9 give +1. An ordered key with signature (0,0,0) can independently select any of the 16 zero-class indices in each slot: 16 × 16 × 16 = 4,096. Repeated indices are allowed in this algebraic count. The signature (1,0,1) similarly gives 9 × 16 × 9 = 1,296.

[Inspect the signature-class diagram](exports/figures/totient-signature-classes.svg). These are derived key triples before phase rotation; equal outer signature values do not require equal outer rune indices. They do not enumerate manuscript locations, enforce mirror-node geometry, or measure how many alternatives survive the complete proposed traversal. Therefore they cannot be used as the denominator of a chance probability for the reading.

### Check one transition by hand: WEATHER → TURNS

WEATHER occupies absolute positions 365–369, where position is `27 × (row − 1) + column`. Its original key-node center is (14,5), position 356, and contains OE with rune index 22. The cumulative phase total before this transition is 2, so the direct-position mode with offset 1 applies.

| Quantity | Calculation | Result |
| --- | --- | --- |
| Next phase | `(1 + μ(365) + μ(366) + μ(367) + μ(368) + μ(369)) mod 3` = `(1 + 1 − 1 − 1 + 0 + 0) mod 3` | 0 |
| Next outer state | Quarter-turned positions are 365, 392, 419, 446, 473; minimum 365 has μ = 1. Update `(1 + 1) mod 2`. | 0 |
| Next signature | Phase 0 and outer state 0 force the middle component to 0. | (0,0,0) |
| Next axis | `μ(365 + 356) + μ(gcd(473,361))` = `μ(721) + μ(1)` = 1 + 1 | Positive: vertical |
| Next boundary role | Three-quarter-turned endpoint has position 257. `(μ(257) + φ(22)) mod 2` = `(−1 + 10) mod 2` | 1: beginning |

For a vertical block, the minimum quarter-turned position corresponds to its bottommost cell. Calling that cell the beginning therefore predicts upward reading. The supplied TURNS block does read upward, from (14,19) to (10,19), and its key has signature (0,0,0). These properties agree; the calculation still does not choose column 19, the block's starting row, its length, or the exact key.

Every transition now has the same level of detail in the report's `calculation` object: coordinates, transformed positions, individual Möbius values, cumulative state, gcd arguments and boundary selection. The independent checker reconstructs these entries by rotating coordinates directly instead of using the replay's formulas for rotated absolute positions.

## A controlled ambiguity: three SOON nodes

The source documents L–C–EA, L–I–EA and L–EO–EA. Their center indices 5, 10 and 12 all have totient 4. All therefore derive L–R–EA, align to EA–L–R, and turn the same X–D–W–H ciphertext into SOON.

However, the next-axis formula also uses the original center's **position**. With the documented centers (25,7), (20,15) and (25,14), the scores are respectively 0, −1 and −1: horizontal, diagonal, diagonal. The published transition fit chooses (25,7), which agrees with THEN's horizontal block. The source explicitly identifies that choice.

This is a bounded example of a selection that affects the result. It does not prove that any desired sentence can be produced, or that all three choices satisfy every proposed navigation condition. It shows why a full decoder needs a rule selecting the original node before the next block is inspected.

## Are three-rune mirrors unusual by themselves?

We counted equal outer runes around any center, along rows, columns and the two diagonals, at every in-bounds radius from 1 to 13. Each unoriented triple is counted once. The map has **507** such mirrors.

As a control, we shuffled the same 729 rune indices 99 times using seed 3301. This preserves rune frequencies but removes their original positions. Mirror counts ranged from **458 to 568**. The observed count is inside that range.

This control is deliberately narrow. It tests the abundance of this simple geometric pattern, not the quality of the proposed English, the complete traversal, or the combined transition rules. It supplies no chance probability for the selected reading. Testing that stronger claim would require a completely specified search procedure, the same search budget on controls, and a scoring rule chosen before inspecting the results.

## How to reproduce

Download this experiment's bundle and extract it without changing its folder structure. Python 3 and its standard library are sufficient; no network, API or model is required.

```text
python experiments/records/totient-map-route/run.py --check
python experiments/records/totient-map-route/check.py
python experiments/records/totient-map-route/signature_figure.py
```

The first command rebuilds the report and coverage image in memory and compares them with the saved versions. It checks all selected key nodes and subtractions, recomputes transition matches, enumerates signature classes, and repeats the mirror controls. Running without `--check` writes the report and coverage image. The explanatory node-choice diagram is an authored illustration of the reported three-node comparison.

The second command independently derives totients through prime factorization, checks all 65 recorded rune subtractions and node-derived keys, and compares totients with coprime counting for 1–729. It also independently verifies all 16 transition calculation records, all 18 key-node midpoints, and rotation identities for all 729 cells. It does not independently rediscover the route or certify the author's navigation choices. The JSON report includes all rune traces, transition inputs/results, the 99 control counts, reused cells, and phase-rotation ablations. Those ablations deliberately change the phase rule; they are sensitivity checks, not alternatives permitted by the fixed phase formula.

The third command independently calculates totients by counting coprimes and Möbius values by factorization, checks all six reported signature-class counts, and verifies the saved diagram. Add `--write` only to regenerate that diagram. It does not search for map nodes or produce plaintext.

## What would strengthen the claim

A useful next variant would freeze a deterministic procedure for choosing the initial node, subsequent anchors, node transformations, distance expressions, block lengths, directions, stopping condition and tie-breaking. It should specify how to handle zero-valued runes and every branch that remains possible.

Run that fixed procedure on an unseen continuation before adjusting it. Report all outputs, not only readable ones. If alternatives remain, bound the enumeration and apply an explicit score to every candidate and to matched controls. This is the distinction between a reproducible selected reading and a decoder capable of making a new prediction. See [search space and bounds](#/wiki/search-space) and [planning a first experiment](#/wiki/first-experiment).

The numerical and thematic correspondences in the source's “Strongest Plaintext Evidence” discussion are not assigned significance here. Nor does this test rule out other 27 × 27, totient or geometric methods. Revisions that change node selection or traversal belong as related variants in this experiment family, with their changed choices stated explicitly.
