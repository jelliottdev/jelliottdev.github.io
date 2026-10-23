## Finding

The 2012 closing message places **131 digits on three physical lines** after “P.S.” A proposed reading turns that ragged block by taking columns instead of lines. We replayed the six fixed readings of the digits alone and four more readings that preserve the **five-character “P.S. ” indent**. **None passes the amended 95% printable-pair screen or matches a pinned longer constant.**

![Printable-pair scores for all ten fixed readings of the 2012 P.S. block.](experiments/records/h03-ps-layout-replay/readings.svg)

The often-mentioned short strings **“3301” and “1033” do not occur in any of the six bare-block readings**. When the visual indent is preserved, “3301” appears once in one column direction and “1033” once in another. They are separate four-digit matches, not a continuous decoded message. The surrounding pair-decoded text does not meet the screen: the indented readings range from **73.8% to 78.5%** printable, against the **95%** threshold. All ten derived 131-digit integers also have explicit compositeness witnesses; primality was a report-only observation, not a hit condition.

## Why the 95% threshold matters

The source initially borrowed an **80% printable** cutoff from a test of arbitrary bytes. A pair of decimal digits can only be 00–99, and **68 of those 100 values** map to printable ASCII characters. The old cutoff therefore produced **37 route firings in 200 random blocks** in the source's own control, before the real P.S. block was tested. The source raised the threshold to **95%** and repeated its controls before examining the real readings. Our independent run also shows the problem: **61 old-cutoff route firings** across 200 newly generated random blocks, but **zero** at 95%. All **10 planted readable blocks** pass the amended gate.

The five-column indent was added as a disclosed extension **after** the six bare readings returned no hits. It is reasonable to inspect the physical layout, but a newly noticed four-digit match is not a predeclared success. We retain the observed strings as observations and apply the same fixed 95% gate to the extra four routes.

## Exact scope and reproduction

The [pinned signed-message text](experiments/records/h03-ps-layout-replay/source/ky_2012-01-final-message.asc) supplies the three digit lines, of lengths **40, 45 and 46**. The source runner refers to a separate local corpus path absent from its pinned checkout; we used the pinned repository's `.asc` copy and verified that its extracted digits exactly match the source's saved results. The test covers only four directions of column reading, the joined lines and their reverse, plus the four indented column readings. It does not test arbitrary widths, rearranged digits, a different numeral encoding or an unknown running key.

From the Liberpedia repository root, run:

```text
python experiments/records/h03-ps-layout-replay/run.py
python experiments/records/h03-ps-layout-replay/check.py
```

The [result](experiments/records/h03-ps-layout-replay/results.json) and [source manifest](experiments/records/h03-ps-layout-replay/source-manifest.json) include the exact input provenance. A separate checker reconstructs all ten routes from the physical lines, checks their scores and short-string counts, and compares them with the pinned source result.
