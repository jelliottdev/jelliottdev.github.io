# Short-seed known-crib controls: preserved results

This research record tests synthetic ciphertexts under two declared hash-based generators. It does not search the unsolved manuscript. The public experiment page and visualizations are still being prepared.

The [frozen protocol](../../plans/seed-crib-controls.md) specifies all six planted fixtures, 8192 candidate generator/seed pairs, five crib lengths and correct/incorrect crib conditions. A crib is an assumed exact plaintext sequence at an exact position. There are 120 result cells. The source plaintext is the 95-rune known-reading trace for LP2-57; new ciphertexts are constructed from it.

## Observed results

With two known runes, all 24 fixture/search/crib combinations retain multiple seeds. In the four combinations with a correct crib and the generating pair included, survivor counts are 4, 6, 11 and 8. Each contains one exact whole-text recovery. The extra candidates do not predict the complete withheld continuation.

The other two-rune searches also retain candidates: 4–5 with the correct generator but its planted seed outside the dictionary; 2–10 with the wrong generator; and 2–8 with an incorrect first crib rune. None of these survivors recovers the complete withheld suffix or full plaintext.

At crib lengths 4, 8, 16 and 32, the four included generating-pair controls each retain exactly their true seed. The other 20 combinations retain no candidates. These are finite, dependent fixtures. Four runes are not a universal sufficient crib length, and an empty dictionary result does not rule out seeds outside the dictionary or other generators.

The complete CSV retains all 120 cells and all surviving seed IDs. The JSON additionally preserves every searched 95-index keystream, all planted inputs and every survivor's complete decoded sequence, exact suffix comparison and number of correct withheld indices. Withheld text is never used to select survivors.

## Reproduce from the repository root

Python 3 standard library only. Use new output paths:

```sh
python scripts/test_seed_crib_controls.py
python scripts/seed_crib_controls.py --output seed-results.json
python scripts/check_seed_crib_controls.py seed-results.json --receipt seed-audit.json
python scripts/summarize_seed_crib_controls.py seed-results.json seed-audit.json --output seed-summary.csv
```

The independent checker imports no producer code. It separately packs seed/counter bytes, reconstructs rejection conversion, checks every candidate stream and uses direct encryption of the assumed crib to test compatibility. Python's hash primitives are a shared dependency. Boundary controls cover the rejected-byte cutoff and byte order; exhaustive three-symbol, two-position fixtures distinguish prefix agreement, suffix agreement and whole-text recovery.

## Scope

Only SHA-256 and SHA-512 with the fixed domain separator, unsigned big-endian seed/counter encoding, rejection conversion and exact additive alignment are tested. Each searched seed dictionary is 0–4095. The deliberately omitted seed is 4096, which remains a valid generator input. No unknown-position search, key skipping, alternate languages, English score or adaptive seed expansion is involved. No statistical probability or one-time-pad identification follows from these controls. Human review remains pending.
