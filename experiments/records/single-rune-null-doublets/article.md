# Does removing one rune type reduce LP2’s adjacent repeats?

No, under the fixed rule tested here. For each of the 29 rune types, remove **every occurrence of that type** from LP2-00–55 and recount equal adjacent runes within pages. The archived stream has **86 doublets**. Every one-type deletion leaves **92 to 109**, so none reduces the raw count. This closes a small, explicit class of null-removal suggestions; it does not test arbitrary null positions or whether deletion before a later cipher could help.

![Adjacent equal-rune counts for every fixed one-type deletion](experiments/records/single-rune-null-doublets/single-rune-null-doublets.svg)

## What was fixed

The inputs are the 56 archived LP2-00–55 page texts and the stored 29-rune alphabet. Headings are included. Within each page, remove non-runes as in the [published doublet census](#/wiki/doublets); never count a pair across pages. For each rune type, delete all its occurrences, leave all surviving runes in order, and count adjacent equal pairs again. The rule has exactly **29 configurations**, not a search over individual positions. The [plan](experiments/records/single-rune-null-doublets/plan.json) and source hashes make the corpus and comparison explicit.

| Result | Value |
| --- | ---: |
| Original adjacent equal pairs | 86 of 12,901 within-page edges |
| Lowest after a one-type deletion | 92 (G, W, S or NG) |
| Highest after a one-type deletion | 109 (R) |
| Fixed-count shuffle expectation after deletion | 437.08–440.80 pairs, depending on type |

Deleting a type can destroy an existing pair of that rune, but it can also bring two formerly separated surviving runes together. For G, five old G–G pairs disappear while 11 new equal pairs form across deleted runs, giving **86 − 5 + 11 = 92**. For R, two old pairs disappear and 25 new bridges form, giving **109**. The [complete result](experiments/records/single-rune-null-doublets/results.json) records the removed symbols, destroyed pairs, new bridges, surviving edges, rate and reference expectation for every type. Its exact bridge accounting is checked independently.

The fixed-count shuffle expectation is calculated separately from each **retained** page’s rune frequencies. The observed-to-expected ratio stays between **0.209 and 0.248** across the 29 deletions. That comparison says the low-adjacency feature is still visible after this transformation relative to a within-page shuffle of the retained symbols. It is **not** a probability that a null model is false, and a shuffled stream is not a plaintext-language model.

## What this does and does not close

If the proposal is specifically “one rune type is padding, and deleting all of it will remove the low-doublet feature from the raw LP2 stream,” these 29 exhaustive cases do not support it. A different claim could delete only selected positions, delete several rune types, preserve word boundaries differently, or delete before applying a cipher whose alignment then changes. Those have much larger search spaces and need separate bounds and controls. A readable fragment after hand-selecting deleted positions would not be comparable with this fixed sweep.

This record measures a ciphertext statistic. It does not recover plaintext, identify a null symbol, or rule out nulls in general. The [null-removal guide](#/wiki/method-nulls) explains the larger family and the order-of-operations issue; the [doublet guide](#/wiki/doublets) defines the 86-pair baseline.

## Reproduce

From the repository root or extracted [experiment ZIP](downloads/experiments/single-rune-null-doublets.zip), using Python 3 standard library:

```text
python experiments/records/single-rune-null-doublets/run.py --check
python experiments/records/single-rune-null-doublets/check.py
```

The producer checks every input hash and reproduces the report and SVG. The separate checker extracts rune streams through a different parser, verifies the destroyed-pair and bridge identity for all 29 cases, and recalculates every edge count and exact fixed-count shuffle expectation. Both compare the same declared source files; neither re-reads the manuscript images.
