## Finding

**One of 21 pre-registered checks flagged the first rune on each physical line. The apparent signal disappears when line wrapping is included in the comparison.** The other nine position checks, six keyless reading families, and five rejection-pattern checks did not meet their declared gates in the pinned source run. Our replay independently reconstructed the 55-page input and all observed position counts, and reran the source's position, rejection, layout, and planted-message controls. The source's six-family message replay is included as a separate result file.

The conspicuous line-start result is real: its rune-frequency statistic is **78.66**, above every one of 200,000 draws from *fixed positions* in the manuscript. But line starts are not random positions. Wide rune glyphs are more likely to be pushed over a line's right margin. When shuffled text is broken into new lines using fitted glyph widths, the mean statistic rises from about **27 to 66**. The observed 78.66 falls within that distribution: **p = 0.177** in the source's 5,000 reflows, and **p = 0.195** in our separately seeded 2,000 reflows. This shows that the frequency excess alone does not establish a deliberate first-rune signal; the reflow model is an approximation, so it does not prove how the original pages were typeset.

![A flat comparison makes line initials look extraordinary; reflowing the shuffled text places the observed value near the ordinary range.](experiments/records/line-initial-layout-control/layout-control.svg)

## What the source tested

The pinned transcription contains **12,956 runes** on **594 physical lines** across **55 nonempty LP2 pages**. We recovered those counts, plus **2,928 hyphen-delimited words**, **219 sentence units**, **86 adjacent identical-rune pairs**, and **four pairs crossing a line**. The source's original plan had two preliminary split-count errors; the published runner corrected them before testing, without changing its gate. Each of its 21 pre-registered checks used a threshold of **0.001 ÷ 21**.

| Check | What it asks | Result |
|---|---|---|
| Ten positions | Are the first, last, second, or penultimate runes of lines, and the edges of words, pages, and sentence units, unusually distributed? | Only **line initials** clear the fixed-position gate. All other nine are negative. |
| Six reading families | Do line initials, per-page acrostics, diagonals, every-Nth-line initials, page edges, or word edges form an English-like message after a bounded set of rune transformations? | All six are negative against a separate *best-of-family* null. Short per-page readings look tempting by raw score but fare worse than the same search on random draws. |
| Five rejection checks | Does the low adjacent-repeat rate change at line or word positions, or does the nonzero difference channel carry a boundary signal? | None clears the gate. The line-boundary test has only **four repeats among 539 transitions**, so its negative result has little power against subtle suppression. |

The reading families enumerate **56,376 candidate transformations** in total. That is a count of variants within six tests, not 56,376 independent ideas. Each family compares its best score with the best score obtained by running the *same search* on size-matched random manuscript draws. The source's two planted English line-initial messages, plain and Caesar-shifted, were both recovered. This checks that its English scorer can recognize a sufficiently strong message in the tested format. It does not test other languages or more complex decoding rules.

For throughput, some message-family nulls were rerun separately from a fresh seed state. Their observed searches are identical to the pinned receipt; their sampled null extrema are independent repeats, not byte-for-byte copies of the source's serial RNG stream. The result file records the actual number of null replicates for each family.

## Why the line-start check changed

The source fitted relative widths for 29 runes and two separators from **539 nonfinal lines**, then used those widths to greedily reflow shuffled rune streams. Our independent fit also produces shorter variation in estimated line widths than treating every rune as equal width (**0.0828 vs 0.1063** coefficient of variation). A width-weighted expectation reduces the observed line-start departure from **78.66 to 38.73**. The source reflow and our independently seeded reflow give compatible results.

One archived precision claim needs correction: the source calls **53.5%** an “exact line-length” fit. Its code counts an existing line if its tokens fit the width budget, without checking whether the following token would also fit. A stricter resynchronised comparison matches **42.9%** of line lengths exactly; **82.5%** are within one token. That is adequate to demonstrate the flat-null confound, but it is not a reconstruction of the original typesetter. The source reports a **0.879** correlation with a BabelStone rune font; that external font file was absent from the pinned checkout and is **not independently verified here**.

## What a negative can and cannot rule out

The source planted a fixed English phrase into synthetic, layout-aware streams in two ways: always write the chosen rune, or let an anti-repeat rule override a collision. With 200 trials per setting, the corrected line-start statistic detected **all** trials when at least **60%** of line initials were forced under either mechanism. At 40%, it detected **59.5%** and **46.0%**, respectively; at 20%, neither setting registered. At zero forcing, the flat statistic falsely fired in **49%** of trials, while the layout-corrected statistic fired in **0 of 200**. These are conditional powers for these two synthetic mechanisms and this phrase, not a bound on every possible hidden message.

![The corrected detector sees both planted mechanisms consistently once sixty percent of line initials are forced, but has little sensitivity below forty percent.](experiments/records/line-initial-layout-control/power-curve.svg)

The tested rejection signature is especially weak at line breaks. A scheme that *prevents* additional boundary doublets can remain invisible with only four observed boundary events. The six reading searches are English-quadgram checks over identity or Atbash, 29 shifts, forward or reversed order, and keeping or dropping the F interrupter. They leave column readings, ornament-defined sets, different languages, and other transformations open.

## Reproduce and inspect

From the repository root, run the independent measurement and checker with Python 3 and NumPy:

```text
python experiments/records/line-initial-layout-control/run.py
python experiments/records/line-initial-layout-control/check.py
python experiments/records/line-initial-layout-control/plot.py
```

The bundled [results](experiments/records/line-initial-layout-control/results.json) give our line-start, line-final, width-fit, planted-control, and reflow measurements. The `replay-armA.json`, `replay-armB.json`, `replay-armC.json`, `replay-layout.json`, and `replay-power.json` files retain each full source-arm replay; the corresponding original scripts, pre-registration, and pinned result receipts are in `source/`. The independent checker builds the ten position sets from a second parser and verifies the observed counts and rejection tables before comparing source receipts. To rerun all 21 source checks, use the commands in the bundled `source/RESULTS.md` at the pinned revision. Its message-family nulls are computationally expensive; inspect the included results and replicate counts first.
