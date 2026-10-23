# Can the rebuilt reader inspect the ornament bands?

The [A-06 source method](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L3-ornaments) proposes reading artwork-adjacent bands with an image-to-rune reader. Its historical **226-class** template file is unavailable. We instead tried the same raw reader with a [freshly rebuilt 229-class bank](experiments/records/dukotah-image-template-rebuild/article.md), clearly as a **new variant**.

## First, can it read known text?

![The fresh raw reader matches 85.4% on LP2-56 and 81.7% on LP2-57; both miss the source's 90% gate.](experiments/records/dukotah-ornament-fresh-reader-gate/solved-reader-gate.svg)

We applied the source's page-reading code directly to the two solved LP2 images, with no supplied rune positions or line lengths. The fresh class-to-rune mapping was fitted on LP2-00–55; **neither solved page was in that fit**. The reader matched **82 of 96** compared positions on LP2-56 and **89 of 109** on LP2-57: **171 of 205, or 83.4% combined**. The source's required calibration is **90%**. It also emitted more runes than the visible text on both pages (96 versus 85; 109 versus 95).

This differs from the [T2 substitution probe](experiments/records/dukotah-t2-fresh-template-loo/article.md), which scored 178 of 178 solved-page rune choices **with the surrounding reference text and positions supplied**. That useful control does not show that the reader can independently extract a line of runes from pixels. The raw-reader result here tests that harder prerequisite.

Because the control failed, **we did not read the ornament bands or score the source's hidden-message hypotheses** with this fresh bank. The archived source inventory still gives coordinates for **109 candidate bands on 39 pages**; that is a list of image regions, not 109 decoded strings. The result says the current fresh reader is not calibrated for a negative finding about those bands. It says nothing about whether artwork contains a message.

## One transcription difference

At rune 80 (zero-based) on LP2-57, the pinned source markdown has `E` in `...DIUINITE...`; Liberpedia's page text has `Y` in `...DIUINITY...`. The rune is on the fifth runic row near image coordinate **(932, 1725)**. The [original page image](images/lp2-57.jpg) and our [row crop](experiments/records/dukotah-ornament-fresh-reader-gate/lp2-57-line5-crop.png) show the **Y-shaped rune**; the raw reader also outputs `Y` there. The primary score above uses the source's own text. Using Liberpedia's reading changes only this comparison, to **172 of 205 (83.9%)**—still below the gate. Neither transcription was silently changed.

## Reproduce

The [frozen variant plan](experiments/records/dukotah-ornament-fresh-reader-gate/variant-plan.json) pins the source revision, fresh bank, both canonical inputs, images and gate before any band-content reading. From the Liberpedia root, with Python, NumPy, SciPy and Pillow, plus the [original images](downloads/original-images.zip) extracted into `images/`:

```text
python experiments/records/dukotah-ornament-fresh-reader-gate/run_gate.py --check
python experiments/records/dukotah-ornament-fresh-reader-gate/check.py
python experiments/records/dukotah-ornament-fresh-reader-gate/plot.py --check
```

The [full predicted and reference rune arrays](experiments/records/dukotah-ornament-fresh-reader-gate/gate-results.json) support an independent recount. This fresh-bank test cannot reproduce the source's missing historical template file or its archived ornament verdict.
