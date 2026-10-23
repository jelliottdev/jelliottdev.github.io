# Can one rune stream unlock another?

An [archived test](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p20_interlocking.py) divides one LP2 page by each rune’s zero-based alphabet index. Indices **2, 3, 5, 7, 11, 13, 17, 19 and 23** go into one stream; all others go into another. These are alphabet positions, not Gematria Primus prime values. It tries a passage from the Old English poem *Deor* as a key for the first stream, then reuses its best output as a repeating key for the second.

**The original script cannot report a hit.** Its coincidence score is between 0 and 1, but its two hit checks require scores above **1.3** and **1.5**. We reproduced its exact output, including zero hits. That zero says nothing about whether the idea works; the gates are unreachable for *any* input.

![The source splits 217 runes into two streams; its original score gates are impossible, while a separate normalized comparison finds no distinctive final-stage score.](experiments/records/wulfic-deor-interlocking-streams/comparison.svg)

## What a corrected comparison shows

We separately multiplied the same coincidence score by 29, a conventional normalization that makes a threshold such as 1.3 possible. We kept the source's key directions, offsets and choice of the best first-stream result. The second-stream maximum is **1.17**. In **110 of 199** seeded shuffles of the page, the *whole two-stage search* reached at least that score. The amended 1.3 screen found no second-stream candidate here. The selected first-stream score, **1.88**, was reached by 18 of 199 shuffles. The first-stage peak alone does not turn into a distinctive final-stage result.

The shuffles preserve the page's rune counts and redo both stages, including the adaptive choice of first key. They show how this exact search behaves under a simple control; they are not an encryption model or a proof that every interlocking cipher fails.

## Exact bounds and reproduction

The source's “page 20” is **current LP2-03**: its 217 rune values match the archived input. It yields 65 prime-index and 152 other runes. The source tries three directions at 600 *Deor* offsets, then three directions at 65 repeat-key offsets. Only the Old English section of the pinned poem is parsed, producing 960 rune values. The separate Caesar-shift check cannot change coincidence score, so all 29 shifts tie on that measure.

Our [pinned plan](experiments/records/wulfic-deor-interlocking-streams/plan.json) and [saved results](experiments/records/wulfic-deor-interlocking-streams/results.json) preserve the source calculation and label the normalized comparison as a later diagnostic. An [input-parser amendment](experiments/records/wulfic-deor-interlocking-streams/input-parser-amendment.json) records that an initial exploratory run mistakenly included the poem's modern translation; the published diagnostic uses the source's 960-value stream. The original source output is saved as a short [trace](experiments/records/wulfic-deor-interlocking-streams/source-run.txt), and `python experiments/records/wulfic-deor-interlocking-streams/check.py` repeats the independent computation and controls. The pinned external checkout can be used with [the source replay wrapper](experiments/records/wulfic-deor-interlocking-streams/replay_source.py).

This is one page, one poem, a value-based split and a fixed repeating-key rule. It does not test other partitions, poems, word boundaries, feedback rules or language-based readings.
