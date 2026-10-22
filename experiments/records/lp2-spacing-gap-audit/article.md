# LP2 spacing: an observed line-gap difference

The supplied discussion proposes reading thick and thin spaces as binary. It does not preserve the screenshots used for the original word-gap examples, so their coordinates cannot be reconstructed from the transcript. It does give one checkable example: **the last row of the LP2-15 number panel sits farther from the preceding row**. This record measures that *line gap* on the archived page image. A line gap is the blank vertical distance between rows; it is not a word gap between adjacent runes on one row.

![Five measured gap comparisons: 62, 61 and 79 pixels in the LP2-15 number panel, with adjacent rune-text controls near 74 pixels.](experiments/records/lp2-spacing-gap-audit/line-gaps.svg)

## Fixed measurement

The [plan](experiments/records/lp2-spacing-gap-audit/plan.json) fixes four image rectangles before classification: the four-number-row panel and lower rune text on LP2-15, plus rune text on adjacent LP2-14 and LP2-16. Every input is the original 2400 × 3600 JPEG, checked by SHA-256. Within each rectangle the script counts a horizontal row as ink when at least five grayscale pixels are darker than 160. Ink rows separated by no more than 14 blank rows form one printed line. The gap is the number of wholly blank rows from one line's last ink row to the next line's first ink row. The [result file](experiments/records/lp2-spacing-gap-audit/results.json) records **every** line's inclusive y coordinates, not just selected gaps.

The panel row boxes are y=876–953, 1016–1093, 1155–1232 and 1312–1389. Their intervening clear gaps are **62, 61 and 79 pixels**. The final one is 17 pixels wider than the larger of the first two. The six rune-text gaps lower on LP2-15 are all 74 pixels. The six LP2-14 text gaps and eleven LP2-16 text gaps range from 73 to 75 pixels. Repeating the extraction at darkness thresholds 100 and 200 preserves the 17-pixel difference between the last panel gap and the earlier panel gaps; at threshold 200 all three panel gaps shrink by one pixel.

These controls show that the panel anomaly is not merely the ordinary one-pixel jitter in neighboring text lines. They **do not** identify its cause. The panel uses decimal numerals and a different layout from the rune text. A separate typesetting or font mechanism could account for it; only editable source or a controlled reproduction could resolve that. The transcript's suggested apostrophe/quotation/fallback-font explanation applies to other examples and was not tested by these selected rows.

## What this does and does not test

Four panel rows supply only three vertical gaps; even a chosen threshold would give at most three bits. There is no documented rule for treating this number-panel exception as a bit, ordering it with other pages, or choosing a character encoding. This experiment therefore publishes **no bitstream or decoded text**. It also does not test the original word-spacing examples because their screenshots are missing and no exact gaps were identified. A proper word-gap test would first publish page, row, adjacent-glyph coordinates and ambiguous marks; then compare predeclared gap classes with ordinary kerning and fallback-font controls before attempting a decode.

To reproduce from the repository root, run `python experiments/records/lp2-spacing-gap-audit/run.py --check`, then `python experiments/records/lp2-spacing-gap-audit/check.py` and `python experiments/records/lp2-spacing-gap-audit/plot.py --check`. The independent checker derives line boxes through a separate byte-row projection and verifies every measured value.
