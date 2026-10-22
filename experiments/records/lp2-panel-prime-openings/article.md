# Does the LP2-15 spiral supply a repeating rune key?

The [LP2-15 number panel](#/wiki/lp2-15-panel?section=construction) has a complete, reproducible construction: Fibonacci values select sixteen prime numbers, whose absolute distances from 3301 fill the printed spiral. A supplied solver proposal asks whether the resulting sequence might act as a key. This experiment tests one finite version of that suggestion. **It finds no exact match** to nine fixed 12-rune openings on LP2-00–55.

![The sixteen selected primes and their modulo-29 shifts, in panel spiral order.](experiments/records/lp2-panel-prime-openings/key-cycle.svg)

## The rule tested

The prime stream in spiral order is `2, 3, 5, 7, 13, 23, 43, 79, 149, 263, 463, 829, 1481, 2593, 4507, 7817`. The last two primes are recovered by the *absolute-distance construction*; simply calculating `3301 − printed value` would give the wrong primes there. The [construction ledger](exports/fibonacci-prime-panel.json) fixes every number and panel coordinate.

For each rune index `c` at position `j`, apply `output = (c + sign × key[(j + offset) mod 16]) mod 29`. The sign is `−1` or `+1`; the offset is one of `0–15`. Every rune advances the key, including a heading rune. Non-rune punctuation does not. Restart at each page and compare the first twelve output runes against the same [nine archived known openings](#/experiments/lp2-fibonacci-openings) used by the Fibonacci-shift baseline. The complete output for every case is saved, not only an opening score.

**Repeating the sixteen numbers is a test assumption.** The page specifies neither a modulo-29 shift nor repetition, direction, starting offset, or which pages should receive the key. We chose this compact family because it changes the baseline's schedule while preserving its input, signs, clock and exact-match criterion. It does not claim to represent every plausible use of the panel.

## Complete result

LP2-50 has no runes in the archived transcription. The remaining 55 pages produce **1,760 cases**: 55 pages × 16 offsets × 2 directions. All 1,760 page outputs are distinct. Against nine fixed openings, that is **15,840 exact comparisons**, with **zero matches**. The [results file](experiments/records/lp2-panel-prime-openings/results.json) retains all output indices and match decisions. Distinct full outputs avoid counting a repeated configuration twice; these comparisons are still highly dependent, not 15,840 independent statistical trials.

This excludes only a continuous cyclic shift stream with these sixteen primes, page-local reset and the declared opening test. A shorter accidental word elsewhere would be a different, much larger search. So would taking prime *indices* rather than values, reversing the spiral, advancing over separators, using autokey feedback or joining pages. Those choices should be declared as separate variants before inspecting their outputs.

## Reproduce

Extract the [experiment bundle](downloads/experiments/lp2-panel-prime-openings.zip) with its folders intact, then run from its root with Python 3:

```text
python experiments/records/lp2-panel-prime-openings/run.py --check
python experiments/records/lp2-panel-prime-openings/check.py
python experiments/records/lp2-panel-prime-openings/plot.py --check
```

The independent checker reconstructs the sixteen primes against the printed LP2-15 cells, verifies the nine opening files, and inverts every transformed rune to its archived input. The figure is generated from the saved key. These checks verify the declared calculation, not the claim that the manuscript intended this cipher.
