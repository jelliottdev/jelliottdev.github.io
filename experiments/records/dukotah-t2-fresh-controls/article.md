## Finding

**The original T2 control programs run on the newly pinned image templates, and their planted changes are usually found.** All **545 valid physical rune splices** were detected and read correctly. Of 604 planted missing runes, **598** were localized; of 604 planted extra runes, **588** were localized. These are strong results for these specific one-change plants. They do not establish that the manuscript has at most one transcription error.

![The physical splice and planted length-error controls recover most synthetic changes, while 26 unplanted lines remain flagged and a separator plant control is missing.](experiments/records/dukotah-t2-fresh-controls/figure.svg)

This follow-up uses the [fresh 229-class image bank](#/experiments/dukotah-t2-fresh-template-loo) and the [pinned source T2 programs](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/T2). The original archived bank reported 226 classes; its arrays are unavailable. The source's shorthand “segments 45–54” means manuscript pages **LP2-45–49 and LP2-51–55** here, since LP2-50 has no rune lines.

| Source control | What happened | What it shows |
| --- | --- | --- |
| C1, solved pages | 178/178 local rune choices agree | The substitution probe passes its 90% entry gate. |
| C2′, physical splice | 545/545 valid planted runes recovered; 189/189 in source segments 45–54 | Its dense-segment recovery exceeds the registered 50% gate. |
| C5, planted missing rune | 598/604 localized | The length probe often recovers a single missing-rune plant. |
| C5, planted extra rune | 588/604 localized | The length probe often finds a single extra-rune plant. |

The splice code requests 200 placements in each of three groups. Some replacement runes do not fit the erased glyph span: **4,774 of 16,184** proposed slot–rune pairs were excluded, leaving 168 solved-page, 189 dense-segment and 188 other valid splices. The high recovery applies to this width-filtered sample.

## What the manuscript measurements say

Using thresholds set from the solved pages, the indel program flags **26 unplanted lines**: 24 on LP2-00–44 and two on LP2-53. It flags none on the solved pages. The source then labels every flag “segmentation” using the direction of a component-count mismatch or equality with the canonical rune count. The [individual flagged rows](experiments/records/dukotah-t2-fresh-controls/out_indel_adj.json) remain available for inspection.

That classification is a **rule applied to image components**, not a ground-truth reading of every flagged rune. Equal component and reference counts cannot rule out a merged pair, a split stroke, or offsetting insertion and deletion. The source's stated 95% bound of at most one real insertion or deletion additionally assumes that synthetic single-error localization transfers to unknown real errors and that detections are independent. This replay verifies the program's plants and arithmetic, but not those assumptions. It therefore **does not certify the number of real transcription errors**.

The separator script reports exact *counts* on **582/604** lines and exact *positions* on **580/604**, including **10/10** solved lines. The **19 older disputed-count lines** now have matching counts under this newer mark classifier. Its `sep19.py` calls these “alignment” cases solely because the counts agree; that label is not an independent manual check of the pixels. The registered C4 control—delete one separator on ten solved lines and require 8/10 lower residuals—has no implementation in the pinned T2 scripts and **was not run**.

## Reproduce

The [frozen plan](experiments/records/dukotah-t2-fresh-controls/plan.json) pins the source revision, image/instrument dependencies and control order. The [results](experiments/records/dukotah-t2-fresh-controls/results.json) link every raw output hash. The independent receipt checker recounts the 545 splices, 1,208 indel plants, 26 flags and separator totals from the saved rows without calling the source's image code:

```text
python experiments/records/dukotah-t2-fresh-controls/check.py
```

For a full rerun, use Python with NumPy, SciPy and Pillow and the [pinned source revision](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/T2). The wrapper verifies source code, all 58 original JPEGs and the fresh instrument, then runs the original scripts in an isolated temporary tree. `--controls-only` uses the bundled, hash-pinned fresh line map and substitution probe; `--rebuild` recomputes those first. Both enforce the solved and dense splice gates before later controls:

```text
python experiments/records/dukotah-t2-fresh-controls/run.py --source-root PATH/TO/liber-primus --site-root . --controls-only --check
```

The original scripts' raw [splice](experiments/records/dukotah-t2-fresh-controls/out_splice.json), [indel](experiments/records/dukotah-t2-fresh-controls/out_indel.json) and [separator](experiments/records/dukotah-t2-fresh-controls/out_separators.json) results are preserved, including the flagged cases and every tested plant. The wrapper compares parsed JSON so platform newline differences do not change the scientific result.
When replaying the bundled Windows line map on a Unix host, the wrapper changes only its filesystem path separators in the temporary copy; line identities and measurements stay fixed.
