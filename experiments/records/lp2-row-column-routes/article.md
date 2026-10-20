# Simple row and column transposition routes

## Why this test?

Reading a page backwards or down its columns is a natural first attempt. But “try transposition” leaves many decisions unstated: the alignment of uneven rows, which corner to start from, whether direction alternates, and whether symbols are also substituted.

This record tests a small, explicit set of pure rearrangements. Its success criterion is exact agreement with one of nine known 12-rune openings at the start of the output. It does not score English or assume every valid plaintext must reuse an existing opening.

## Plan and input layout

The plan and runner were committed as `26802b6` before execution. Use all archived LP2-00–55 text, retaining recognized runes and grouping them by source line. Headings remain included. Non-rune characters and lines without runes are ignored. LP2-50 remains an explicit zero-rune page and produces no routes.

Rows are left-aligned by rune ordinal, not by measured image coordinates. The first rune of every nonempty line is in ordinal column zero. Short rows remain short; missing cells are skipped, not padded. This convention can differ from the manuscript's physical column alignment.

## The sixteen route choices

| Choice | Options | Meaning |
| --- | --- | --- |
| Main axis | Rows / columns | Visit a complete row or ordinal column at a time |
| Outer direction | Forward / reversed | Top-to-bottom versus bottom-to-top rows; left-to-right versus right-to-left columns |
| Initial inner direction | Forward / reversed | Left-to-right versus right-to-left within a row; top-to-bottom versus bottom-to-top within a column |
| Alternate inner direction | No / yes | Keep the same direction, or reverse it on every other visited row/column |

The product is 2 × 2 × 2 × 2 = 16 parameter routes per nonempty page. Alternation begins with the selected initial direction and changes by visited-group ordinal, not by the original printed row number. Some routes or output strings can coincide; 16 is a parameter count, not a claim of 16 distinct texts on every page.

No substitution, fixed shift or repeating key is applied. A pure transposition uses every source position once and keeps its rune value.

## Hand-checkable ragged-row controls

For the invented rows `ABC`, `DE`, `F`, ordinary column-first reading gives `ADFBEC`. Row-first reading with alternating directions gives `ABCEDF`. These are implementation controls only, not manuscript inputs or results.

The independent checker verifies those controls and constructs every real route by sorting source coordinates with a separate ordering-key implementation. It checks that each saved route is a complete permutation and every output index comes from its declared source position.

## Results and limits

All 880 parameter routes completed across the 55 pages with eligible runes. No output's first 12 indices matched any of the nine fixed known-reading openings. There are 7920 exact opening comparisons in total.

The nine opening vectors come from Warning, Welcome, Some Wisdom, first koan, Loss of Divinity, second koan, Instruction, LP2-56 and LP2-57. Their exact values and source-trace hashes are recorded in the plan. They were fixed before this search.

This negative result is limited to those openings, these routes and the archived layout convention. It does not rule out other beginnings, arbitrary column permutations, spirals, rectangular reflow, physical coordinate alignment, a different region, or transposition combined with substitution. There is no probability claim or general readability score.

## Follow an output back to its source

Each page has a `source_positions` array. Every entry gives its zero-based source ordinal, one-based archived line, one-based rune position within that line, and alphabet index. Each candidate's `source_ordinals` array is the output-to-input mapping: its first number tells you which original position supplied output position zero.

The accompanying `output_indices` array contains the corresponding rune indices. The `alphabet` list maps indices back to rune symbols. Original whitespace and punctuation are not part of the permutation.

The diagram shows the first six positions of the ordinary column-first route on LP2-31. It is extracted from the saved result, not an invented grid. All 269 positions are retained in that route's complete trace.

## Reproduce

Use Python 3.12.10 and the repository checkout. No third-party package or network service is required.

```
python experiments/records/lp2-row-column-routes/run.py --check
python experiments/records/lp2-row-column-routes/check.py
```

The first command regenerates and compares every source position, route, output index and match decision. The second uses the independent ordering-key checker. Both reject discrepancies rather than silently replacing the saved result.

[Download all routes and source traces](experiments/records/lp2-row-column-routes/results.json). To save another report, run the main script with `--output my-routes.json`; it refuses an existing filename. The plot script reads the saved result and draws one trace without searching again.

## Retest and review

Codex reran the complete enumeration and verified all 880 candidates with the independent ordering implementation on 20 October 2026. No route rule, layout choice, opening vector or matching criterion changed after the first run. The checker and diagram were added afterward for verification and explanation. Human review remains pending.

## Related work and next variants

The [fixed-alphabet experiment](#/experiments/lp2-alphabet-warning-prefix) includes whole-stream reversal with shifts and a different opening criterion. The [transposition guide](#/wiki/transposition) explains the documented historical 14-column permutation. Neither record establishes that every transposition on an unsolved page has been searched.

A physically aligned column model, a justified spiral, a new region or an added substitution needs a separately planned variant. Preserve its source-coordinate trace so another reader can tell exactly which operation was performed.
