# Are the 86 doublets clustered by page or position?

The low overall doublet count is established for the archived LP2-00–55 rune streams. A separate question is where the 86 surviving equal-neighbor events fall. This record compares their locations with **two explicitly conditional placement controls**, so a short page is not treated as if it offered as many opportunities as a long one.

![Observed zero-doublet pages, page-count variance, shortest event gap and page-edge events shown against length-aware random-placement ranges.](experiments/records/doublet-placement/placement.svg)

| Measurement | Observed | Fixed-total placement: central 95% | Fixed-page-count placement: central 95% |
| --- | ---: | ---: | ---: |
| Pages with no doublet | 13 of 55 | 8–17 | Fixed at 13 |
| Page-count variance / mean | 1.204 | 0.715–1.483 | Fixed at 1.204 |
| First or last five within-page edge slots | 4 | 1–8 | 1–8 |
| Shortest gap between event starts | 6 runes | 1–7 | 1–6 |
| Median gap | 113 runes | 81–127 | 83–117 |
| Gaps of five runes or less | 0 | 0–6 | 0–6 |

An event occupies the left edge index of an equal adjacent rune pair. The input has **12,901 available within-page edges** on 55 nonempty pages; LP2-50 has no alphabet runes. For gap measurements, place the filtered page streams one after another in LP2 numerical order and subtract the starting rune coordinates of consecutive events. The resulting 85 gaps include comparisons across page boundaries, but no *event* is created across a page boundary. The shortest actual gap is six runes, on LP2-27. “Gap” here is a distance between event starts, not the [alphabet distance between extracted doublet symbols](#/experiments/doublet-event-lags).

## Why 13 empty pages is not itself surprising

Under the first control, choose 86 distinct edge slots uniformly from all 12,901 available slots. This keeps the observed total and the actual page lengths but lets each page's event count vary. Using each page's length, the exact expected number of nonempty pages with **zero** events is **12.25**. Ten thousand seeded placements yielded a central range of 8–17; the observed 13 sits inside. The raw count variance-to-mean ratio is 1.204, likewise inside its length-aware range. Shorter pages have fewer chances to contain an event, so a crude equal-length Poisson comparison would answer a different question.

The 13 zero-doublet pages are LP2-05, 07, 13, 14, 15, 17, 28, 31, 37, 38, 40, 49 and 53. Their mean rune length is 214, versus about 242 for the 42 pages with at least one event. The complete output lists every page's length, count and event index. This difference in means is descriptive; the length-aware placement result is the relevant control for the zero-page count. No page style or section classification is inferred from these numbers.

## Are neighboring events kept apart?

With the total-only placement control, the minimum gap reaches six or more in **540 of 10,000** trials. With the second control, which keeps each page's observed doublet count fixed and randomizes only its event positions, it does so in **451 of 10,000** trials. The absence of gaps one through five is therefore near the edge of both reference distributions, while the median gap of 113 and the four events in the first or last five edge slots lie within their central ranges.

These tail fractions are exploratory. The minimum-gap observation was already known when these controls were chosen, and a uniformly selected set of edge slots does not reproduce every way a rune stream can make overlapping equal pairs. Natural-language EA positions, punctuation policy and a real key schedule could each alter gap behavior. The controls help specify a future mechanism test; they do not identify one.

## Reproduce and extend

Extract the ZIP with its directory structure. Python 3.12 and the standard library suffice:

```text
python experiments/records/doublet-placement/run.py --check
python experiments/records/doublet-placement/check.py
```

The producer stores input hashes, all 86 event slots, page lengths, exact zero-page expectation, simulation seeds, central ranges and inclusive rank counts. The independent checker extracts the runes another way, compares every event to the published [source-location ledger](#/wiki/doublets?section=counts), and recomputes the exact zero-page expectation from binomial coefficients. Run `--write` to regenerate the JSON and SVG. The analysis is conditional on the archived transcription; it does not settle uncertain glyphs or compare an independent complete transcription. For the boundary treatment of these same events, read the [separator audit](#/experiments/doublet-boundaries).
