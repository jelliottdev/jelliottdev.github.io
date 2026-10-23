# Can word cribs predict a periodic key?

The archived solver tries familiar words at each visible word slot, converts each guess into votes for a repeating key, and chooses the most-voted value at each key position. We replayed its two stated examples: archived `page_30` with period 17 and `page_27` with period 43. Those files are **LP2-13** and **LP2-10** in the current reader; their rune text matches exactly.

## The check that matters

We inferred a key from half the visible word slots, then read the untouched half. Across both pages, both folds and all three source directions, **none of the untouched words exactly matches an encoded source-dictionary word**. The source's full-stream vocabulary scores are 10–19, but those count substrings anywhere in the joined rune text. They are not 10–19 independently recovered words.

![The key voted from half the word slots predicts no exact dictionary words in the untouched half, and known-message controls fail.](experiments/records/wulfic-periodic-word-crib-votes/heldout.svg)

The stronger caution is the **known-message control**. We encrypted source-dictionary words with a planted period-17 or period-43 key and applied the same vote and holdout procedure. The best fold recovered 11 of 31 untouched eligible words; several recovered none. All 12 planted folds miss the predeclared 50% recovery requirement. Thus this particular vote heuristic is not validated as a detector. Its failure on LP2 cannot exclude periodic keys.

## What the source actually tests

The implementation checks whether each proposed word gives a consistent key **within that word**. It then tallies votes for each key residue independently. Although its description promises consistency with *other* word slots, the code does not require a complete mutually consistent sentence or key. The source's three directions also include equivalent subtraction/addition reconstructions under signed keys; those are alternate parameterizations, not independent confirmations.

The dictionary has 335 source entries, 309 distinct GP rune words after encoding. The page and period pairs were examples in the script, not periods established by this experiment. A 199-shuffle whole-selection reference was computed across both pages, all three directions and both folds, but **its rank is not interpreted** because the positive control failed. This record measures the specified solver, not the entire periodic-key family.

Four related source scripts validate candidate phrases against `data/gpu_hill_checkpoint_gpu1.json`; that checkpoint is absent from the pinned public tree. We have not replaced it with another key or described those validations as reproduced. The separate `lp_crib_drag.py` uses a different linked-position rule and is outside this record.

## Repeat it

From a clone of [the pinned source revision](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c), run `python experiments/records/wulfic-periodic-word-crib-votes/run.py --source-root PATH_TO_CLONE --check` to recalculate all saved rows and controls. The independent `check.py --source-root PATH_TO_CLONE` extracts the original dictionary directly from the source, reconstructs the six unrefined keys and twelve holdout scores, and checks the source stdout receipts. Omit `--check` to regenerate the saved outputs.
