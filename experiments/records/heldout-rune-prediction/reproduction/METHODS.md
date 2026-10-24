# What the fixed D-02 test measures

This is a newly specified finite test of the published proposal, not a replay of an existing higher-order program. A good next-rune prediction is evidence about that predictor. Failure does not prove randomness, an OTP, an absence of plaintext, or the exclusion of a cipher family.

## Inputs and prediction

The input is the source parser’s first 55 percent-separated segments: 12,956 GP29 rune indices. These are source segment ordinals, not physical page numbers 0–54. The final source segment maps to LP2-55. The exact transcription remains an external, hash-validated input for publication.

Even and odd source segments form two fixed folds. One fold trains the model; the other is scored, then they swap. Training contexts reset at every segment boundary. Test contexts use only previous runes in that same segment; test labels never update training counts. Every order scores the same segment positions after the first eight runes, for 12,516 held-out positions. Reported bits per rune are total negative log2 probability divided by that common count.

For each order 1–8, the fixed-order KT model uses `(count(symbol,context)+1/2)/(count(context)+29/2)`. An unseen context gives probability 1/29.

Every predictor also reports gain over the uninformed uniform guess: `log2(29) − observed loss`, where `log2(29) = 4.857980995127572` bits per rune. Positive gain means a shorter predictive code than that guess; zero or negative gain does not. A loss below the filtered-control band can result from less count overfitting or more unseen contexts. It does not by itself establish a gain over uniform prediction. This reference is a reporting diagnostic, not an additional metric or a changed gate.

Raw gains are retained, but gains within ±0.0000000001 bits per rune are described as numerically equivalent to uniform. This avoids calling summation roundoff an improvement. The 26 measurement values and selection gate are unchanged.

The PPM-C model starts at its declared maximum order. At each lower context, symbols already observed in unsuccessful higher contexts are excluded. For remaining counts with total N and D distinct symbols, a seen symbol has probability `count/(N+D)`, while an unseen symbol escapes with probability `D/(N+D)`. Empty effective contexts escape with probability one. If every remaining alphabet symbol is observed, the model closes the escape and uses `count/N`. After all contexts escape, order −1 is uniform over the remaining symbols. These choices specify one PPM variant; other escape and adaptation rules are not tested.

## Compression and provenance

LZMA is a separate whole-stream compression arm, not a frozen-model held-out likelihood. Two exact source views are retained: one rune per byte and the minimally sized big-endian base-29 integer encoding. Both use the source’s preset 9 plus extreme mode, with the default XZ container. The packed view failed to detect all synthetic planted examples; it cannot support an exclusion merely because a manuscript score is ordinary.

Five dispersion metrics average rolling Pearson count dispersion over every valid window at widths 29, 58, 116, 232 and 464. Lower values indicate greater local balance. Three drift metrics measure four-bin and eight-bin monogram independence and an eight-bin linear frequency trend; higher values indicate greater variation. These measurements do not identify a human, deck or machine generator.

## Common reference and selection

Each of 1,000 seeded controls runs the source’s continuous soft filter: draw a uniform rune; if it repeats the previous output, resample once with probability 0.83. The replacement may still repeat. The rule matches uniform marginals and repeat scarcity in expectation, not exact counts. All models receive the same streams; there is no per-model control selection.

There are 26 predeclared measurements: eight KT losses, eight PPM losses, two compressed sizes and eight provenance statistics. Each candidate is appended to the common reference. Tail directions are fixed, and all 1,001 rows participate symmetrically in each column’s mean and population standard deviation. An exactly all-equal column contributes zero. Each row’s family score is its largest directed Z value. The inclusive family rank counts controls at least as large, plus the candidate itself, divided by 1,001. The fixed gate requires a family fraction below 0.01 and at least one strict marginal tail beyond the reference’s linear one-percent tail boundary. No order, metric or suppression parameter changes after target inspection.

This rank is conditional on the selected filtered-uniform reference. It is not a universal probability that a text is random. Gross synthetic recovery, disrupted-order, fold-mismatch and independent filtered validation results are retained, including every method-specific failure. They demonstrate selected capacities and implementation behavior, not sensitivity to every possible structure.
