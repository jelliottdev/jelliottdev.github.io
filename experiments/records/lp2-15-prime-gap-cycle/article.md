# Does the LP2-15 prime-gap tail repeat?

A supplied proposal finds **8, 20, 10, 6** at the end of the LP2-15 spiral prime gaps after reduction modulo 28. The numbers are correct. The pattern appears **once** in the fifteen shown gaps. Extending the same [Fibonacci-indexed prime construction](#/wiki/lp2-15-panel?section=construction) gives **4**, not the predicted **8**, for the next gap.

![The shown tail, its period-four prediction, and the different next four residues.](experiments/records/lp2-15-prime-gap-cycle/gap-cycle.svg)

The source's 4×4 array is a **derived prime array**, not the decimal values printed on LP2-15. Following its spiral gives `2, 3, 5, 7, 13, 23, 43, 79, 149, 263, 463, 829, 1481, 2593, 4507, 7817`. All fifteen reported consecutive differences and modulo-28 residues check out. The last four residues occupy gap positions **12–15** and occur nowhere else as an exact consecutive four-number run in the shown data.

Before extending the sequence, we fixed the proposal's most direct cycle reading: repeat the final four residues for the **next eight** gaps, without rotating or searching phases. The next Fibonacci prime index after 987 is 1597; its prime is 13477. Thus the first new gap is `13477 − 7817 = 5660`, and **5660 mod 28 = 4**.

| Continuation | Next eight residues mod 28 |
| --- | --- |
| If the four-number tail repeats | 8, 20, 10, 6, 8, 20, 10, 6 |
| Same Fibonacci prime-index generator | **4, 2, 20, 2, 24, 26, 26, 26** |

None of the eight positions matches the fixed cycle. This is a check of **one arithmetic recurrence claim**, not a test of rune decryption or an exclusion of other panel paths. The proposal does not explain why to use modulus **28**; the Gematria Primus alphabet has **29** runes. Changing modulus or mapping residues to runes would require a separately stated rule. For a declared comparison, these eight gaps modulo 29 are `5, 4, 7, 12, 25, 10, 22, 22`; no plaintext is inferred from them.

## Reproduce

From the checkout or [experiment ZIP](downloads/experiments/lp2-15-prime-gap-cycle.zip), run from the root of the extracted bundle:

```text
python experiments/records/lp2-15-prime-gap-cycle/run.py --check
python experiments/records/lp2-15-prime-gap-cycle/check.py
python experiments/records/lp2-15-prime-gap-cycle/plot.py --check
```

The [frozen plan](experiments/records/lp2-15-prime-gap-cycle/plan.json) fixes the tail, eight-step continuation and no-phase-search criterion. The [source-number transcription](experiments/records/lp2-15-prime-gap-cycle/source.json) preserves the full array, gaps and residues with the three supplied screenshots identified by SHA-256; the screenshots themselves are not republished. The [results](experiments/records/lp2-15-prime-gap-cycle/results.json) retain all 24 primes and 23 gaps. The producer checks the source array against the archived [LP2-15 construction ledger](exports/fibonacci-prime-panel.json); the independent checker rebuilds the primes with a sieve.
