# Autokey seeds from an archived search

**Result.** Four related source searches found no output that passed their stated hit screen. This is a result for those seeds, pages, six feedback rules, and the source's one-rune and frequency checks. It does not rule out autokey on Liber Primus.

![Four source search branches and their hit counts](experiments/records/wulfic-autokey-seed-families/screen.svg)

| Source branch | Settings | Passed its one-rune check | IoC above 1.3 |
| --- | ---: | ---: | ---: |
| 22 named keyword seeds | 4,488 | 135 | 0 |
| Every two-rune seed | 171,564 | 5,058 | 0 |
| Every three-rune seed | 4,536,354 | 0 | 0 |
| A distinct four-rune DEOR seed | 60 | Not required | 0 |

The first three branches come from an [archived comprehensive autokey script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/autokey_comprehensive.py). It tries plaintext and ciphertext feedback, each with subtraction, addition, and Beaufort arithmetic modulo 29. Each page restarts its seed. For the named, two-rune, and three-rune branches, **every isolated one-rune word** must decrypt to I or A before the output's normalized index of coincidence (IoC) is considered. The fourth row is the one [P21–30 source variant](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p21_30_autokey_solver.py) with a different DEOR seed; its screen uses IoC alone.

These are four **search branches**, not millions of independent solving ideas. The 34 archived source pages numbered 21–54 correspond to LP2-04–37 in this site. The comprehensive script skips pages with fewer than three isolated one-rune words for its three-rune seed search, leaving 31 pages. The P21–30 variant covers ten pages. Seventeen of its other keyword arrays duplicate the comprehensive branch on those pages, so they were not counted again here.

## What the controls show

A constructed 261-rune passage, derived from an independently recorded solved reading, passed the source's screen after we encrypted it under each of the six feedback rules. Two- and three-rune planted seeds were also recovered by their complete searches. The detector can therefore find a deliberately planted, reading-like example with its declared assumptions.

For the manuscript, we repeated each **whole branch**, including its seed search, on 49 within-page rune shuffles. The best named-keyword IoC (1.121) was equaled or exceeded by 44 controls; the two-rune best (1.177) by 24; the four-rune DEOR best (1.064) by 42. The three-rune branch had no candidate past its one-rune gate, so a best-IoC comparison is not informative. These controls preserve page lengths and rune counts; they are a search comparison, not a model of how the manuscript was encrypted.

There is a further limit to this screen. With **ciphertext feedback**, the decoded runes after the seed-length prefix depend only on ciphertext and the selected rule. Changing the seed changes just that short prefix. On a long page, the whole-page IoC and one-rune positions beyond it therefore cannot identify a ciphertext-feedback seed. The planted test verifies this: a wrong seed still passes those ciphertext-feedback screens.

The one-rune I/A requirement is also a hypothesis about the visible word breaks. A seed eliminated by that condition may still be relevant under another segmentation or language. No branch produced an established reading, and the source's zero-hit result is not evidence against every autokey design. A more discriminating follow-up would specify an independent predicted passage or another feature that changes with the seed.

## Reproduce and inspect

The [frozen plan](experiments/records/wulfic-autokey-seed-families/plan.json) states the page mapping, six recurrences, gates, controls, and exclusions before the manuscript results. [Full results](experiments/records/wulfic-autokey-seed-families/results.json) include every page's counts and each complete-search control. Run `python experiments/records/wulfic-autokey-seed-families/check.py` for an independent scalar check, or `python experiments/records/wulfic-autokey-seed-families/run.py --check` to repeat the full grid. [Source parity checks](experiments/records/wulfic-autokey-seed-families/source_parity.py) additionally require a checkout of the pinned upstream commit.
