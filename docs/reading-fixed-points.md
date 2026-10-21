# Unchanged runes in the four-section LP1 object

The interruptions guide now includes the explanation, audited counts, phone-reviewed figure and reproduction downloads. Atbash, Vigenere and word-length guides cross-link it. The extracted reference bundle reproduces every audited position and the SVG; targeted search aliases open the new section directly.

This descriptive audit checks the four known-reading sections underlying the 464-word column-balance object. They contain 1,796 runes. Counts refer to aligned rune positions, not words or the number of different symbols.

| Section | Runes | Unchanged | Recorded interruptions | Ordinary fixed points |
| --- | ---: | ---: | ---: | ---: |
| Warning | 184 | 2 | 0 | 2 |
| Welcome | 515 | 11 | 11 | 0 |
| First koan | 778 | 34 | 0 | 34 |
| Second koan | 319 | 100 | 2 | 98 |
| Total | 1,796 | 147 | 13 | 134 |

Ordinary Atbash preserves index 14. The first koan's shifted Atbash preserves index 1. The Welcome key has no zero residues. The second koan's 13-position key has four zero-valued slots: ordinary transformation at those consumed slots preserves the input index. Those positions still consume a key value; the recorded interruptions do not. A fixed point is therefore not evidence of an interruption.

`scripts/audit_reading_fixed_points.py` independently checks all saved trace rows against original rune order, the section/page mapping and declared arithmetic. It checks every Vigenère key counter and slot, every interruption flag and each output index. Original text hashes match the frozen 464-word plan. The original reproduction implementation was separately rerun: all four complete traces exactly match the saved CSVs, and every reconstructed literal page reading matches its published control.

`exports/reading-fixed-points.json` preserves the source hashes, section totals and all 147 unchanged positions with zero-based page and section ordinals. Reproduce with a new output path:

```sh
python scripts/audit_reading_fixed_points.py --output fixed-point-replay.json
```

The result uses known keys and previously aligned interruptions. It does not infer an unknown skip rule, test statistical significance, count unchanged words, or define a grille. A grille proposal still needs explicit carrier coordinates, placement, orientation and readout order; selecting unchanged runes alone does not supply those rules.

## Arithmetic and LP2-56 extension

`scripts/audit_fixed_point_extension.py` checks the stored GP values against independently enumerated primes and sums the baseline positions by rune. The 134 ordinary fixed points sum to **4,826**, an even composite number. The 13 interruption runes sum to **26**. The reported 4,759 total does not reproduce for this 134-position set. The difference is 67, but that arithmetic alone does not identify which position or convention produced the earlier total; do not invent an omitted-rune explanation.

Adding the explicitly separate LP2-56 known control adds 85 runes and four unchanged positions. Ordinals 16, 50 and 70 consume prime-minus-one shifts 58, 232 and 348, each divisible by 29; their key counters advance normally. Ordinal 56 is the one recorded interruption, and its key counter remains 56. The combined five-section object therefore has 1,881 runes and 151 unchanged positions: 137 ordinary fixed points plus 14 interruptions. It is not the original 464-word object.

The extension auditor checks all 85 trace rows against original rune order, prime enumeration and key counters. The original LP2-56 reproduction also matches its stored literal reading. `exports/reading-fixed-point-extension.json` retains the per-rune GP subtotals, all four extension positions, source hashes and combined counts. This remains a descriptive known-reading audit, not a new grille test or a statistical claim.
