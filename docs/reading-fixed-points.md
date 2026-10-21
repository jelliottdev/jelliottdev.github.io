# Unchanged runes in the four-section LP1 object

Computation complete; public explanation, figure and download registration pending.

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
