## Finding

**The image-reading pipeline runs on all 56 original LP2 JPEGs, but its saved output does not reproduce exactly.** The fresh run finds the same **646 line bands** and **13,140 full-height glyphs** as the archived run. It groups the glyphs into **229 shapes**, compared with **226** archived, and finds **233 lines** whose rune count matches the reference text, compared with **232** archived.

![The fresh image read and archived run agree on line bands, but differ slightly in shape classes and count-matching lines.](experiments/records/dukotah-image-template-rebuild/pipeline.svg)

Only **4 of 646** line-band glyph counts changed: one on LP2-08, two on LP2-22, and one on LP2-54. The fresh run reads eight fewer glyphs in total. The 226-class figure is a saved result, not a required check in the code; the reader accepts every shape class seen at least 100 times. Its fresh 229-class bank selects 33 templates, while the archived bank selected 32. A fresh run can therefore be used as a **new, explicitly pinned instrument**, but it must not be presented as the original archived array or as proof that the reference transcription is correct.

## What the stages establish

The original programs first locate line bands, collect glyph images, group similar shapes, and then choose a low-cost sequence of those shapes for each line. Those stages do **not** read the canonical rune transcription. We used the [pinned source code](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/retranscribe) without changing its rules and checked every hosted image against the source's byte hashes.

The final program compares the image-derived sequences with the LP2 reference text. It first aligns lines by length. The **233 count-matching lines** are a useful check on segmentation, but a matching length alone does not prove that the runes match. The program then learns a mapping from shape classes to rune letters **using those same lines** and reports **95.83% agreement on them**. It uses **zero held-out lines** and does not train on solved LP1 pages. This percentage is an in-sample fit, not an independent transcription accuracy estimate.

We do not know why the fresh and archived shape counts differ. A single-thread run and a stable-sort diagnostic still produced 229 classes. The original archived NPZ arrays have no available hashes, so their contents cannot be compared byte for byte. This record does not settle any disputed rune or test a cipher.

## Reproduce

The [plan](experiments/records/dukotah-image-template-rebuild/plan.json) pins the 56 image hashes, original code, canonical text and historical reports. The [results](experiments/records/dukotah-image-template-rebuild/results.json) hold the fresh artifact hashes; [line counts](experiments/records/dukotah-image-template-rebuild/line-counts.json) allow a separate checker to redo both count-based alignments without using the source program.

The compact check takes seconds from a Liberpedia checkout:

```text
python experiments/records/dukotah-image-template-rebuild/check.py
```

For the full image rebuild, use Python with NumPy, SciPy and Pillow, and a checkout of the [pinned source revision](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1). The wrapper verifies all source and image hashes, copies them into a temporary directory, then runs the four original programs in order. This takes several minutes and does not overwrite the saved results:

```text
python experiments/records/dukotah-image-template-rebuild/run.py --source-root PATH/TO/liber-primus --site-root . --rebuild --check
```

The checker verifies the compact receipts and, when given source and artifact directories, their bytes. It does **not** classify image pixels independently. Any follow-on test using these new arrays must identify them by their hashes rather than silently inherit the archived 226-class result.
