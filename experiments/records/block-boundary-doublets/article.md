## Finding

If a block operation prevents adjacent repeats *inside* each block but leaves ordinary repeat chances *between* blocks, the few repeats should collect at block boundaries. That concentration is absent for the page-start-anchored sizes raised in prior discussion: **18 of 86** doublets at size 5, **13** at size 7, and **6** at size 13. Conditional on each page's observed doublet count, the expected counts are **17.1**, **12.1**, and **6.4**.

![Observed doublets at size-five, seven and thirteen boundaries compared with controls.](experiments/records/block-boundary-doublets/boundaries.svg)

We also searched sizes 2–29 and every shared offset: **434 placements**. The strongest is size 12, offset 8, with 15 events versus 7.1 expected. But **2,181 of 3,000** matched randomizations produced an equal or stronger best standardized excess somewhere in that same search. Choosing the best-looking size after inspection therefore supplies no evidence for this fixed-boundary model.

## What was counted

For each page, remove non-rune characters and mark every equal pair at neighboring rune positions. The edge from rune position *i* to *i + 1* has phase `(i + 1) mod block size`; phase zero is the ordinary boundary when counting restarts at each page. The run preserves the complete 86-event ledger in its JSON output. It never joins pages or assumes that a slash or hyphen restarts a block.

The control randomly places exactly the observed number of events within each page's available edges. That deliberately conditions on the scarce overall count and asks only whether **placement** has a periodic signature. It does not model language or an encryption process. A cipher with a separate starting phase on each page, variable-size blocks, or interrupted counter could evade this particular test; those rules would need to be fixed and tested separately.

## Reproduce

Python 3.12 and its standard library suffice:

```text
python experiments/records/block-boundary-doublets/run.py --check
python experiments/records/block-boundary-doublets/check.py
```

The first command repeats all 3,000 seeded controls. The second independently recounts the event positions and fixed-size boundary hits. The [machine-readable result](experiments/records/block-boundary-doublets/results.json) records every page's event positions, input hashes, selected-search control, and the three fixed-size comparisons.
