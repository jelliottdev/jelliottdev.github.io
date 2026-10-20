# Eleven-rune windows in the Wing and Tree section

Across six pages, **seven windows sum to 563 and ten sum to 569**. This record supports recurrence under the rules below, not statistical significance, intent or decipherment.

## What changed from the grid experiment?

The baseline rearranges LP2-32 into an 11×11 grid and selects a row, column and perimeter. This variant expands the input to LP2-27–32 and selects every consecutive eleven-rune window within each page. It retains prime values and fixed targets 563 and 569. It does not test the perimeter target 1136. The family comparison lists every changed scope field.

## Complete counting rules

Read the archived text in order, including headings. Keep only the 29 alphabet runes. Remove punctuation and line markers, but start a fresh stream at each page. Sum runes 1–11, then 2–12, continuing to the last complete window. A page with N runes contributes N−10 windows. Do not reverse, pad, wrap or cross a page boundary.

| Page | Runes | Windows | Sum 563 | Sum 569 |
| --- | ---: | ---: | ---: | ---: |
| LP2-27 | 234 | 224 | 0 | 2 |
| LP2-28 | 269 | 259 | 2 | 2 |
| LP2-29 | 277 | 267 | 1 | 2 |
| LP2-30 | 263 | 253 | 0 | 1 |
| LP2-31 | 269 | 259 | 3 | 3 |
| LP2-32 | 121 | 111 | 1 | 0 |
| Total | 1433 | 1373 | 7 | 10 |

All window sums total 784505, giving a mean of approximately 571.38. The ledger retains all 1373 windows, including nonmatches. Each includes its rune sequence, sum, one-based rune interval and zero-based source character offsets.

## Why the 569 column is not counted on LP2-32

The first grid column selects positions 1, 12, 23, …, 111. Those positions sum to 569, but are not consecutive. The first grid row uses positions 1–11 and is counted here. A column and a sliding window use different selection rules.

## Limits

Both the targets and section were chosen after the original correspondence was noticed. Adjacent windows share ten runes. Counts cannot be treated as independent trials or p-values. There is no shuffled corpus or adjustment for other targets, lengths and layouts searched. This record does not resolve image-only claims about unspecified row alignments.

## Reproduce and independently check

Extract the experiment ZIP with folders intact, or use the repository. No external packages, images, network requests or AI calls are needed.

```text
python experiments/records/wing-tree-eleven-rune-windows/run.py --check
python experiments/records/wing-tree-eleven-rune-windows/check.py
```

The first command runs the shared census implementation and compares the saved report. The independent checker reads page JSON, constructs intervals by their ending position and sums each directly. It verifies every sequence, coordinate and total without importing the census implementation. Both text representations derive from the same archive: agreement is a computational check, not an independent visual review of the manuscript.
