# Does trimming page margins reveal a special line alignment?

A source discussion suggested reading “shed the circumference” as an instruction to remove manuscript margins and place pages side by side. It described this as something to try, not as a finished decryption. A side-by-side picture is easy to make but easy to overread: text lines can align because pages share a layout. This experiment asks the narrower, measurable question: **do adjacent LP2 pages line up more distinctively than other pages of the same design?**

![All 36 fixed-crop row-alignment scores among LP2-40–48; outlined cells are adjacent pairs](experiments/records/page-margin-row-alignment/row-alignment.svg)

## What was fixed

The nine original JPEGs LP2-40–48 are all 2400 × 3600 pixels. This is a continuous run of text-heavy pages with the same plant-border design; the source proposal did **not** designate these pages. From every image, take the same rectangle, x = 650–1749 and y = 620–2899. This sheds both illustrated sides and keeps the central writing. Preserve the original y coordinates: no page is shifted to fit another.

For each y row, sample every third x pixel. Call the row occupied when more than 12 samples have grayscale value below 90. The similarity of two row masks is their occupied-row intersection divided by their union (Jaccard score). Compare all **eight consecutive pairs** with **all 28 nonconsecutive pairs** from the same run. The [plan](experiments/records/page-margin-row-alignment/plan.json) fixes the crop, threshold, score and controls; [results.json](experiments/records/page-margin-row-alignment/results.json) gives every pair and each page’s row bands.

## What the pages show

The mean score is 0.764 for consecutive pages and 0.672 for controls. That difference by itself is not evidence of a special join: four adjacent pairs score exactly 1.000, **but six nonadjacent controls also score 1.000**. In particular, every pair within LP2-44–48 has the same row mask under this rule. The text grid is reused across multiple pages, so an apparently perfect horizontal alignment cannot identify the correct next page. LP2-40’s enlarged red initial and the larger gaps on some earlier pages also change the measured bands. Every pair, including poor fits, appears in the figure and result file.

This tests only vertical placement of dark text rows after one fixed crop. It cannot tell whether the final rune of one line continues at the beginning of another, whether a word crosses a page boundary, or whether “shed the circumference” refers to physical page margins at all. The source left crop, page order, registration and success condition open. Selecting those *after* seeing an attractive join would create a large search space. The observed score difference has no significance test because pair comparisons share pages and the groups were not random independent samples.

## Reproduce or extend

Run `python experiments/records/page-margin-row-alignment/run.py --check` and `python experiments/records/page-margin-row-alignment/check.py` from the repository root or extracted bundle. They require Python 3 and Pillow. `run.py` checks each JPEG’s SHA-256 and the complete saved result; `check.py` scans the image buffers independently and recomputes all 36 scores. `plot.py` regenerates the SVG.

A stronger visual continuation test would need a page sequence and a predeclared rune-level seam rule, plus nonadjacent pages matched for template and line count. The [page-join sensitivity record](#/experiments/page-join-sensitivity) separately measures what happens to word statistics when text transcripts are joined or split at page edges. Neither result supplies an LP2 plaintext.
