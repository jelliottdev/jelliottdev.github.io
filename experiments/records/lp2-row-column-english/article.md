# Do simple row or column routes reveal text?

**Question.** If a whole page is read by rows or ordinal columns instead of its printed order, does any route become English-like without changing the runes?

**Result.** One route scores higher than most matched shuffles, but it is **not a deciphered passage**. The best of **848 eligible routes** reads LP2-22 by columns from right to left, downward within each column. Its 131 runes begin `WRRJJTMUXWSIAUJEWXEIANGNEN…` and score **−6.890** under the fixed English model. In **16 of 256** full-route searches on shuffled pages, the strongest control scored at least that high (global add-one estimate **17/257 ≈ 0.066**). This comparison accounts for trying 16 routes on each page; it does not account for choosing the entire route family after examining many other ideas.

![The first five source positions of the strongest route and its score against complete shuffled-route searches.](experiments/records/lp2-row-column-english/route-scores.svg)

## The route and comparison

This uses the **same 16 rules** as the earlier [row-and-column record](experiments/records/lp2-row-column-routes/article.md): row or column first, either outer direction, either initial inner direction, and a fixed or alternating inner direction. Every one of the **55 rune-bearing LP2-00–55 pages** contributes 16 complete permutations, for **880 parameter routes**. A column is defined by the rune's position in its archived text row, with rows left-aligned and missing cells skipped. These are *ordinal* columns, not measured physical columns in the page image.

The routes include reversing the runes within each archived row while keeping the rows in their original order, including on [LP2-15](#/page/lp2-15). Schematically, `ABC / DE → CBA / ED`, with `/` separating rows; this is an invented example, not manuscript text. Rune values stay unchanged while their order changes.

The earlier record asked whether any output started with one of nine fixed known 12-rune readings. This extension reads and scores **the full output** instead. Every rune is retained. Canonical GP Latin labels are scored by overlapping English four-letter groups; 32 routes on two short pages did not reach the predeclared 100-group minimum. The remaining **848** are eligible. Some parameter routes can produce the same output, so 880 counts settings, not guaranteed distinct texts.

In each control trial, we shuffled rune indices **within each page once**, leaving its rune inventory and row lengths intact, then reran all 16 routes on all pages. The best observed score is above the median control maximum (**−7.022**), but **16** whole-grid controls matched or exceeded it. On LP2-22 the leading source positions are line 2, rune 24; line 2, rune 23; line 3, rune 23; line 4, rune 23; then line 1, rune 22. They yield `W R R J J`, not an independently meaningful phrase. All **16** inverse-permutation controls planted a known decoded GP reading into the LP2-31 row shape, recovered it exactly, and scored **−4.324**, showing the route and scorer can recognize a planted complete passage.

The modest score excess is a reason to leave the exact output inspectable, **not evidence of a cipher solution**. It could reflect chance, text layout, or features of the English scorer; no continuous reading emerged. This test covers only the archived left-aligned row/column convention with pure transposition. Catalog item **9.2** also suggests diagonal routes and other grids, which this record does not test. Physical alignment, spirals, arbitrary column permutations, a second cipher layer and other languages remain outside scope. The catalog is an idea list, not evidence that someone previously ran this exact search.

## Inspect and reproduce

[`results.json`](experiments/records/lp2-row-column-english/results.json) saves all **880** observed scores, the complete best output, and all **256** full-search control maxima. Run `python experiments/records/lp2-row-column-english/run.py --check` and `python experiments/records/lp2-row-column-english/check.py` from the repository root (NumPy and Numba required). The independent checker reconstructs every route from structured page JSON, verifies all source coordinates against the pinned earlier trace, and recomputes the observed and shuffled grids.
