# The zero and capital O characters in the LP2 grids

**The current transcription has 65 digit zeroes and seven capital `O` characters in 70 grid cells.** Two cells contain `00`, so there are 72 round marks in total. The coordinate register below covers every cell written with either character in the 256-entry wiki grid. The source-pixel contact sheets make it practical to inspect the whole set, including cells where the two archived text sources agree.

This is an input audit for [LP2-49–51](#/wiki/alphanumeric-grids), not a decoding result. A numeral conversion, bit image, checksum, or path can change if even one of these two shapes is copied incorrectly.

## Inspect the printed forms

Each panel below arranges **unscaled pixel crops** from a pinned original 2400 × 3600 JPEG. The small label gives page, grid row and column; adjacent characters may appear to the left or right of the target cell. Open a panel at full size or consult the complete [LP2-49](#/reader/lp2-49), [LP2-50](#/reader/lp2-50), and [LP2-51](#/reader/lp2-51) images. These are navigation aids for a human review, not OCR output.

![Seventeen LP2-49 grid cells with a zero or capital O, labeled by grid row and column.](experiments/records/grid-round-glyphs/round-glyphs-lp2-49.png)

![Thirty LP2-50 grid cells with a zero or capital O, labeled by grid row and column.](experiments/records/grid-round-glyphs/round-glyphs-lp2-50.png)

![Twenty-three LP2-51 grid cells with a zero or capital O, labeled by grid row and column.](experiments/records/grid-round-glyphs/round-glyphs-lp2-51.png)

In this manual pass, the seven entries transcribed with `O` have the broader, rounder form, while the numerous zeroes are narrower. The strongest nearby comparisons are LP2-50 row 2 (`1O` beside `0u`) and LP2-51 row 6 (`2O` beside `00`). I did not identify a definite conflict with the stored `0`/`O` readings. This is **not** independent human certification of all 72 shapes: the coordinates were selected from the transcription, and other characters mistaken for neither `0` nor `O` would be missed. The [JSON coordinate register](experiments/records/grid-round-glyphs/results.json) gives every original crop rectangle for further review.

| Page | Grid row, column | Transcribed capital-O entry |
| --- | --- | --- |
| LP2-49 | 6, 2 | `1O` |
| LP2-49 | 10, 6 | `2O` |
| LP2-50 | 2, 6 | `1O` |
| LP2-50 | 13, 5 | `2O` |
| LP2-51 | 4, 8 | `1O` |
| LP2-51 | 6, 5 | `2O` |
| LP2-51 | 8, 1 | `2O` |

The separate seventh-onion and wiki transcriptions differ at [five grid cells](#/wiki/seventh-onion-transcriptions?section=grid), but none is a `0`/`O` difference. Their agreement is useful for locating a mark; it is not a second photographic observation.

## What the byte assumption adds—and does not add

Under the [conditional base-60 rule](#/wiki/alphanumeric-grids?section=unique-base), `0` has digit value 0 and `O` has value 24. Sixty of the zeroes are the **first** character of a pair. Replacing one of those with `O` gives a value of at least `24 × 60 = 1,440`, outside a byte. Five zeroes occur as the **second** character: swapping four of them to `O` still fits a byte, while `40 → 4O` would become 264. All seven printed `O` characters occur second, and swapping any of those to `0` remains byte-valued.

This arithmetic constrains readings **only if** every pair is meant to be one unsigned byte with that digit order. It must not be used as independent proof of the printed letter or the intended encoding. The [direct-byte experiment](#/experiments/grid-direct-bytes) kept the current `0`/`O` readings fixed; its negative result therefore does not cover all conceivable round-glyph changes.

## Reproduce the register

From the repository root, or with the experiment ZIP and the named image files extracted alongside it:

```text
python experiments/records/grid-round-glyphs/run.py --check
python experiments/records/grid-round-glyphs/check.py
```

The first script verifies source SHA-256 hashes, produces the same three contact sheets, and records the 70 source coordinates and conditional byte alternatives. It needs Python 3 and Pillow; it makes no network or AI calls. The second script independently rebuilds the entire 256-entry grid from the structured page records and checks every coordinate, token and alternate value. Neither script identifies printed glyphs automatically. The [plan](experiments/records/grid-round-glyphs/plan.json) states the inclusion rule and limitations.
