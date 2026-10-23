## Finding

**A fresh image-template bank makes the same rune choices as the archived T2 probe on all 604 lines.** The two runs do not have identical measurements: their candidate costs differ on **329 lines**, and selected image positions differ on **262**. The ten solved LP2 lines pass the source's first control, with **178 of 178** tested positions agreeing with the documented reading.

![All 604 lines retain the same best rune sequence, while costs and measured positions change on many lines.](experiments/records/dukotah-t2-fresh-template-loo/figure.svg)

This is a **fresh variant of the original substitution probe**, using the 229-class template bank rebuilt in [the image-pipeline audit](#/experiments/dukotah-image-template-rebuild). The archived T2 bank reported 226 classes, and its original arrays are unavailable. Identical rune choices do not mean that the historical image measurements were reproduced exactly.

## What was tested

The [pinned T2 program](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/T2) aligns each manuscript line against a reference rune sequence. It then temporarily opens one position, compares the 29 possible rune labels at that position, and restores the reference labels around it. We ran its original line mapper and substitution probe on **58 byte-matched JPEGs**: LP2-00–55 and the two solved pages LP2-56–57. No thresholds or source algorithms were changed.

The solved-page control was run **before** the full probe. Those ten lines were absent from the fresh class-to-rune label fit, so this control is held out from that fit. The probe still uses each line's reference length and neighboring rune labels. Agreement on the unsolved pages therefore tests local consistency with the supplied transcription; it is **not an independent reading of those pages from pixels**.

| Page group | Tested positions | Same as reference | Different choices |
| --- | ---: | ---: | ---: |
| LP2-00–44 | 10,951 | 10,916 | 35 |
| LP2-45–49 and LP2-51–55 | 1,992 | 1,992 | 0 |
| Solved LP2-56–57 | 178 | 178 | 0 |

The archived and fresh probes also agree on the *best rune sequence* for every one of the 604 lines, including the 35 positions where that sequence differs from the reference. That stability is useful evidence about this particular local substitution test. It does not settle disputed word breaks, insertions, deletions, or manuscript transcription as a whole. The source's separate physical-splice, indel and separator controls were not rerun here.

The source calls the 91-line group “segments 45–54.” Its page mapping skips runeless LP2-50: these segments correspond to manuscript pages **45–49 and 51–55**. The checker asserts that mapping for every compact row.

## Reproduce

The [frozen plan](experiments/records/dukotah-t2-fresh-template-loo/plan.json) lists the 58 image hashes, source revision, source program hashes and the fresh instrument hashes. The [compact line receipt](experiments/records/dukotah-t2-fresh-template-loo/line-results.json) preserves each line's reference and best rune indices, candidate costs and positions for both runs. The independent checker recounts all 13,121 comparisons and the source-versus-fresh differences without calling T2's scoring code:

```text
python experiments/records/dukotah-t2-fresh-template-loo/check.py
```

To rerun the original source programs, obtain the [pinned source revision](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus), then use Python with NumPy, SciPy and Pillow. The wrapper checks all image, source and instrument hashes, creates an isolated temporary tree, runs the solved-page gate first and only then runs all pages. It does not alter the source checkout or saved receipts:

```text
python experiments/records/dukotah-t2-fresh-template-loo/run.py --source-root PATH/TO/liber-primus --site-root . --rebuild --check
```

The same wrapper can compare an already generated isolated source tree with the saved receipt using `--artifact-root PATH/TO/isolated/liber-primus --check`. The bundled [template bank](experiments/records/dukotah-t2-fresh-template-loo/templates.npz) and [class mapping](experiments/records/dukotah-t2-fresh-template-loo/diff_report.json) fix the *fresh* instrument exactly; they do not substitute for the missing historical NPZ.
