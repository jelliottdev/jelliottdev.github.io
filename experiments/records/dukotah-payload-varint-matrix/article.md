# Can the LP2 grid bytes describe doublet gaps?

The [source's E‑02v test](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round28/L5/PREREG.md) treats the 256-byte LP2-49–51 grid payload as a sequence of base-128 integers. It asks whether those integers rise and fall with the distances between adjacent repeated runes elsewhere in LP2. This extends our [earlier seven-reading check](#/experiments/payload-doublet-gaps) to the source's **three byte versions and all 24 stated comparisons**.

![Across three pinned byte versions, the strongest rank correlations are 0.119, 0.119 and 0.117, far below the source's 0.5 gate.](experiments/records/dukotah-payload-varint-matrix/varint-gap-matrix.svg)

**All 24 rows reproduce the source's saved result; none reaches its stated effect-size gate.** Each byte version was decoded as both LEB128 and MSB-first base 128, reading bytes forward or backward. Each of those four streams was compared with 85 distances between repeated-rune events and with a related 86-value sequence that starts at the first event's position. The strongest absolute Spearman rank correlation is **0.1187**, against a required **greater than 0.5**. Because no row crosses that first gate, the source's 100,000-permutation second stage is not invoked.

This tests a specific *numeric reading* of the grid, not whether repeated runes matter or whether the payload encodes something else. The three byte versions differ, but their best correlations are nearly identical. The [complete row table](experiments/records/dukotah-payload-varint-matrix/results.json) preserves decoded lengths, compared lengths and signed correlations, so the small differences are inspectable.

## How it was checked

The four pinned inputs are exact source bytes: three 256-byte payload versions and its 12,956-byte LP2 rune stream. That stream has 86 adjacent repeat events; their 85 distances start **85, 249, 197, 129, 127**. We independently decoded and ranked each of the 24 cases, then compared each rounded row with the source's archived output. The original source reports **10/10** planted gap-sequence recoveries and **0/50** random-payload hits. Our separate positive check re-encodes all 85 real gaps in both base-128 orders, recovers them exactly and obtains correlation 1.

The [local plan](experiments/records/dukotah-payload-varint-matrix/plan.json) fixes inputs and rules for this replay, but it follows an already published source result; it is **not an independent preregistration**. The source's controls are archived receipts, whereas our positive check and independent 24-row recount were run here. Arbitrary byte transformations, start offsets, gap definitions and cipher mechanisms remain outside the test.

Run from the repository root with Python 3:

```text
python experiments/records/dukotah-payload-varint-matrix/run.py
python experiments/records/dukotah-payload-varint-matrix/check.py
python experiments/records/dukotah-payload-varint-matrix/plot.py
```
