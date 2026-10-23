# Does the archived fractionation test reverse its own shuffle?

The archived proposal puts the 29 rune values in a keyword-mixed 6×5 grid. Each rune becomes a row and column number; the proposal then tries several ways to rearrange those numbers. We replayed its **14 keywords on six intended LP2 pages**. The historical page filenames were checked against the rune streams: source `page_38`, for example, is LP2-21, not LP2-38.

## The decisive control

Before looking for a reading, a reversal must be able to undo the matching forward shuffle. We planted a known rune message at each target length, each keyword and each of the seven column widths. The archived reversal restored **112 of 588** messages exactly. It failed the other **476**, because it allocates a full-height slice to short columns. A separately labeled inverse using the columns' actual lengths restored **all 588**. The correction is an implementation repair, not evidence that this is the manuscript cipher.

![The archived reversal restores 112 of 588 planted messages; the corrected inverse restores all 588.](experiments/records/wulfic-adfgvx-fractionation/reversal.svg)

## What the manuscript run found

The source names **1,260 settings**. Its own length rule skips **336** split settings, leaving **924 scored settings**. Two cross its vocabulary-score gate: `CABAL`, width 7 on LP2-28, and `CONSUMPTION`, width 19 on LP2-30. Both produce invalid grid cells (8 and 33 respectively). The score omits invalid cells when forming words, so these hits need inspection rather than a reading claim. The source's other gate, **raw IoC above 1.3, can never fire**: its IoC formula always returns a value between 0 and 1.

The separate corrected inverse has **588 settings** on the same pages, keys and widths. Two cross that same heuristic gate: `CARNAL`, width 29 on LP2-27, and `CABAL`, width 7 on LP2-28. They produce 15 and 8 invalid cells. The `CABAL` row is identical under both reversals at that particular stream length. No setting here provides a verified coherent page reading.

The direct route simply fractionates and defractionates each observed rune, returning the original cipher stream. It is a useful identity control, not a decipherment. Four named split points always produce too few pairs and are skipped by the source rule. The source also includes two running-key tests after this grid; those are different methods and are outside this record.

## Repeat the check

Download the experiment files and run `python experiments/records/wulfic-adfgvx-fractionation/run.py --check` to verify the saved outputs against the pinned page JSON. `python experiments/records/wulfic-adfgvx-fractionation/check.py --checkout PATH_TO_WULFIC_CLONE` additionally reads the pinned source commit, verifies all six historical page mappings, and independently checks all 1,512 scored route outputs and source scoring. Omit `--check` on the first command to regenerate the outputs. The source checkout must resolve commit `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`.

This bounds the specified keys, six pages, widths, split rules, and coordinate shifts. It does not test other transposition keys, coordinate encodings, null conventions, or a general fractionation cipher family. The source's vocabulary score and unnormalized IoC are exploratory filters; neither is a calibrated probability of a correct decryption.
