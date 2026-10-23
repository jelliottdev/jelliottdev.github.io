## Result

**The thirteen pages with large red initials do not have unusual spacing under this uniform-page comparison.** Their largest consecutive run is two pages; a random set of thirteen pages has a run of at least two **96.8%** of the time. Their first and last marked pages are LP2-00 and LP2-57, so their span is the full release; that cannot be unusually short. The variance of the twelve internal gaps is **12.85**; **32.8%** of 100,000 random sets have at least that much variance. This tests page placement, not whether the artwork carries a message.

![The published total-red selection, corrected large-initial pages, and two planted spacing controls on the same 58-page axis.](experiments/records/red-initial-presence-order/page-order.svg)

The top row reproduces the [published total-red page list](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/D-illustration-dropcap/RESULTS.md). Its highlighted LP2-07 and LP2-53 are [small red text, not large initials](#/wiki/red-initials). The corrected row has thirteen pages. LP2-03 and LP2-33 each have two large initials; this test deliberately reduces each page to a single yes/no mark.

## What was compared

The [image audit](research/red-initials-audit.csv) freezes which of the 58 LP2 pages contain a large red connected shape. The comparison draws **100,000** uniform 13-page subsets without replacement. It asks whether the actual pages have unusually variable internal gaps, a short overall span, a long run of adjacent pages, or an unusually compressible 58-bit presence string. Span and run probabilities are also counted exactly over all **3,155,581,562,280** possible 13-page subsets. Five declared tail directions are considered together; none approaches the adjusted threshold.

| Measure | Observed | Comparison result |
| --- | ---: | --- |
| Variance of the 12 gaps | 12.85 | 32.8% of random sets are at least as variable; 67.4% are no more variable. |
| Span, last minus first | 57 pages | All 13-page sets have a span of 57 or less. |
| Longest consecutive run | 2 pages | 96.8% of random sets have a run of at least two. |
| zlib size of the packed page bits | 16 bytes | 99,977 of 100,000 random sets also occupy 16 bytes; this score has almost no resolving power here. |

The comparison deliberately assumes every 13-page placement is equally likely. It is a baseline for visible spacing, **not** a model of how the manuscript was composed. A rule based on section boundaries, the identities of the initials, or two initials on one page is outside it.

## Can these checks detect a planted pattern?

The lower two rows of the figure are fixed controls with the same thirteen marks. Approximately even spacing gives a very small gap-variance tail in the sampled comparison, while thirteen consecutive marks give an exact short-span and long-run probability of **46 / 3,155,581,562,280**. But both controls have low gap variance: that one statistic cannot tell even spacing from a single compact block. The evenly spaced control still compresses to 16 bytes, so the compression check would miss that visible regularity. These limitations matter when interpreting the ordinary manuscript result.

The earlier study also tested red-pixel centroids and an initial-rune string. Those are **not** reproduced here: its total-red mask includes two pages without initials, its centroids include all red marks rather than only the large shapes, and several pages have a second or later initial. A corrected identity or position test needs explicit annotation of each large initial before scoring.

## Reproduce

Download the [original JPEGs](downloads/original-images.zip) if you want to repeat the image classification itself. With Python 3 and Pillow, NumPy and OpenCV installed, run `python scripts/audit_red_initials.py > research/red-initials-audit.csv`. The page-order test then needs only Python's standard library:

```text
python experiments/records/red-initial-presence-order/run.py --check
python experiments/records/red-initial-presence-order/check.py
python experiments/records/red-initial-presence-order/plot.py
```

The [plan](experiments/records/red-initial-presence-order/plan.json) pins the image-audit table and analysis rules. [Results](experiments/records/red-initial-presence-order/results.json) retain every observed statistic, tail count and planted control; the [separate check](experiments/records/red-initial-presence-order/check.json) verifies the exact arithmetic and repeats the gap comparison with another random stream. This is an exploratory correction after the source classification error was seen, not a preregistered test of all ways the manuscript could encode information.
