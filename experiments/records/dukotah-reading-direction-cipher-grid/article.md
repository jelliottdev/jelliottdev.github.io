# Reading directions with simple ciphers

Could changing the order of a page's lines and then applying a familiar cipher reveal a complete passage? A pinned Campaign VII program tried five reading orders with 37 fixed cipher settings. We replayed all **10,175 complete outputs** on its 55 unsolved rune-bearing pages. **No output reached the source's fixed −5 quadgram-score threshold.** Its best page scored **−6.717**; the known *Parable* reading scored **−4.421** on the same scale. In 49 complete shuffled searches, **40** found a best score at least as high as the manuscript's. Higher scores are more English-like under this particular model; the threshold does not by itself certify a readable passage.

![The best manuscript output sits among complete shuffled-search results, while the known reading is far higher.](experiments/records/dukotah-reading-direction-cipher-grid/comparison.svg)

| Reading order | What happens to a page |
| --- | --- |
| Rows | Read lines in their archived order. |
| Reverse | Reverse the complete rune sequence. |
| Alternating rows | Reverse every other line. |
| Columns | Read down ordinal rune positions; skip missing positions in short lines. |
| Reverse columns | Reverse that column output. |

Each route is followed by direct reading, Atbash, 28 nonzero shifts, both arithmetic signs for three prime-related streams, and subtraction of a repeating `DIVINITY` key. This is **one grouped search of fixed settings**, not thousands of different ideas. The [source program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/reading_direction.py) and its [archived result](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/reading_direction_results.json) fix the methods and model. The original program did **not** run our 49 shuffle comparisons; those are an added whole-search control.

The best unsolved output came from [LP2-49](#/reader/lp2-49): reverse its ordinal-column reading, then subtract seven from every rune index. Its opening is `NJLTDIGNORWEOFTNGCOBSEOE...`, not a coherent passage. This is the exact program winner, not a visually selected fragment. The archived source's winner and the best score for every route match our replay after its three-decimal rounding.

The program's source text has 55 nonempty unsolved segments; LP2-50 has an alphanumeric grid but no transcribed runes, so the source skips that segment and source segment 50 corresponds to LP2-51. All 57 source segments, including LP2-56 and LP2-57, match the site's archived rune sequences exactly under that mapping. The source's straight-through LP2-57 *Parable* passes its −5 threshold. LP2-56 is a known **enciphered** page and does not pass by direct reading, so it is not treated as a direct-English positive. We additionally encrypted the *Parable* page with shift seven and rearranged it into both alternating-row and ordinal-column layouts. The declared routes recovered every rune and crossed the threshold. These plants check the machinery on a readable text, not its power for every conceivable manuscript reading.

The shuffle control preserves each page's rune counts and line lengths, then repeats the **entire 10,175-setting search** before taking one best score. Its median maximum was **−6.625**. The manuscript's −6.717 is lower than 40 of the 49 control maxima; the one-sided empirical estimate with a +1 correction is **41/50 = 0.82**. This does not establish a cipher model or a universal probability of a reading. It shows that the source's best score is not unusual for this specified search and simple null.

This result is limited to these five layout conventions, these 37 cipher settings, the complete source pages, and one English quadgram scorer. It does not close physical image-coordinate routes, a rule for selecting only some runes, other keys, resets, or non-English passages. The earlier [pure row/column route test](#/experiments/lp2-row-column-routes) tested opening matches without a cipher; this record adds the exact archived route-plus-cipher grid.

The [plan](experiments/records/dukotah-reading-direction-cipher-grid/plan.json) freezes the source bytes and added controls. The [results](experiments/records/dukotah-reading-direction-cipher-grid/results.json) include each page's winning setting and all 49 complete-search controls. From a checkout or extracted bundle, run:

```text
python experiments/records/dukotah-reading-direction-cipher-grid/run.py --check
python experiments/records/dukotah-reading-direction-cipher-grid/check.py
python experiments/records/dukotah-reading-direction-cipher-grid/plot.py --check
```

The checker separately parses the source text, reconstructs the five traversals and 37 transformations, and recomputes every grid maximum. Its floating-point score comparisons use a tight tolerance because its summation path differs from the source's.
