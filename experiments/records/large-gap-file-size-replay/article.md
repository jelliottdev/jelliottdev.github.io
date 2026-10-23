# Do “big-gap” pages have larger JPEG files?

An earlier comparison named 16 pages with unusually wide line gaps and 15 comparison pages, then claimed a **74 KB** difference in their average JPEG size. The page lists are useful because they let us check the arithmetic without choosing a new sample.

![The original size labels average 582.8 KiB for the reported big-gap pages and 542.9 KiB for the comparison pages, a difference of 39.9 KiB.](experiments/records/large-gap-file-size-replay/file-size-comparison.svg)

## What we found

The 16 printed size labels total **9,325 KiB**, giving the reported mean of **582.8125 KiB**. The 15 comparison labels total **8,143 KiB**. Their mean is **542.8667 KiB**, not the post's **508.9375 KiB**. Correcting that arithmetic reduces the difference from roughly 74 to **39.9458 KiB**. This correction matters even before considering any statistical comparison.

All 31 printed size labels match the corresponding [archived JPEGs](#/downloads) when each byte length is divided by 1,024 and rounded **up** to an integer. Using the precise byte lengths gives a **39.83 KiB** difference. The two group medians are about 564.2 and 529.0 KiB, respectively. The [result file](experiments/records/large-gap-file-size-replay/results.json) lists every one of the 58 LP2 JPEG sizes and its SHA-256 hash, including the 27 pages not chosen in the original comparison.

As a scale check, we repeatedly split these same 31 files into groups of 16 and 15 at random. In 100,000 seeded splits, **17,278** had a mean difference at least as large as the observed one in the same direction. That is a *descriptive reference for these fixed files*, not a probability that the gap observation is false: the original groups were not randomly assigned and were selected after looking at the manuscript.

## What remains untested

The supplied discussion names the pages and reports a typical **109-pixel** large gap, **73-pixel** ordinary gap, and **129-pixel** exception on the parable page. Its original screenshot coordinates are absent from the supplied text. This record therefore accepts the author's page labels **only as labels for the file-size replay**. It does not independently establish which pages have a large gap, which glyphs caused one, or whether the space encodes anything. JPEG size varies with page content and encoding; a size difference alone cannot identify a font or cipher mechanism.

To reproduce, run `python experiments/records/large-gap-file-size-replay/run.py --check`, `python experiments/records/large-gap-file-size-replay/check.py`, and `python experiments/records/large-gap-file-size-replay/plot.py --check` from the repository root. The independent checker recalculates the original sums and checks all 31 file-size labels against the archived originals.
