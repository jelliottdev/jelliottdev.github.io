# Can earlier ciphertext runes supply the key?

**Result.** The tested feedback rules produce no supported English reading on the **52 previously untested pages**. Across **1,054,976 full-page settings**, none reaches the source's **−5.2** signal line. The strongest output scores **−6.1758** on [LP2-49](#/reader/lp2-49). In **15 of 32** shuffled searches, the strongest output scores at least as highly; the plus-one comparison is **16/33 ≈ 0.485**.

![Actual feedback-rule outputs score below the source signal line, while known Warning controls score above it.](experiments/records/d04-remaining-page-feedback/feedback-pages.svg)

The [earlier source replay](#/experiments/dukotah-ciphertext-feedback-coefficients) covered LP2-00, LP2-05 and LP2-20. This record applies its exact coefficient, seed and sign grid to the remaining 52 nonempty pages of LP2-00–55. It adds target pages to the same method family; the million settings are parameter combinations, not a million solving ideas.

## The feedback rule

For each rune, the proposed key adds a constant seed to weighted earlier **ciphertext** values, modulo 29. The decoder then adds or subtracts that key from the current ciphertext rune. It is different from feedback using guessed plaintext, because the earlier ciphertext is already known.

We retain all **5,072 source coefficient vectors**: 28 nonzero one-tap values; 840 nonzero two-tap pairs; and 4,204 three-tap vectors whose third tap is limited to **0, 1, 28, 2 or 27**. Each runs with constant seed **0 or 1**, either decode sign and offset zero: **20,288 settings per page**. Feedback is zero for the first `k` runes of a depth-`k` rule, exactly as in the source. Pages are scored in full using the original GP transliteration and English quadgram model.

The best result uses depth three, coefficients **9, 23 and 27**, constant seed **1**, and subtraction on the **66-rune LP2-49**. Its full output is saved for inspection, but its model score does not establish a reading.

## Why the faster decoder preserves this source rule

The source permits paths that skip key positions. In this particular grid, every key-seed position contains the same constant. Moving the key pointer therefore cannot change the decoded rune at a fixed ciphertext position. Every admitted path emits the same plaintext indices; the source's many tied paths differ only in their key pointers.

We evaluate that single plaintext directly while preserving the source's initial-rune convention and score normalization. Before target scoring, **52 source comparisons**—48 seeded random ciphertexts and four repeat-heavy cases—produce identical plaintext and exactly matching scores. The source coefficient lists also match exactly. Additional independent checks cover the first and last vectors at each history depth and both known-reading rules; all source score differences are zero.

This equivalence applies to the constant-seed domain. It does not justify replacing the beam for a varying reference-text key, and these constant-seed tests provide no evidence about recovery from key skips.

## Known messages and complete searches

Before the manuscript run, we encrypt the complete **184-rune Warning** reading under coefficient **7**, subtraction, and each tested constant seed. The constructed ciphertexts exactly match the source encoder. Each **complete 20,288-setting search** places its true rule at rank one, recovers every Warning rune and scores **−4.4784**, above −5.2. Using the wrong unit coefficient instead scores **−7.7142** and **−7.4302**.

These controls test recovery and selection inside the actual grid. They do not establish equal power for every English passage or a general feedback-cipher exclusion.

Each of 32 reference trials independently permutes every target page, preserving its length and rune counts, then repeats the complete 52-page search. Fifteen reference maxima meet or exceed the actual maximum. This compares equally searched opportunities; a permutation reference is not a generative account of LP2. The fixed source signal line is reported separately from that global comparison.

## Scope and verification

The **new target grid took 2.253 seconds**, after compilation, source-parity checks and controls. The **32 complete reference searches took 75.058 seconds**. An independent implementation reads the source coefficient lists and scorer table, calculates feedback with a separate loop, and checks **all 1,054,976 observed scores exactly**. It also checks all 32 null-winning cases and independently repeats the full planted searches. It does not independently exhaust every alignment of every null trial; the producer performs those complete reference searches.

The earlier three-page grid and this extension together cover the named constant-seed coefficient grid on all 55 nonempty pages. They do not cover arbitrary third-tap coefficients, other seeds, reference-text keys, other offsets, plaintext feedback, other languages or additional cipher layers. No source-wide exclusion follows from these bounded searches.

```bash
python experiments/records/d04-remaining-page-feedback/run.py --check
python experiments/records/d04-remaining-page-feedback/check.py
python experiments/records/d04-remaining-page-feedback/plot.py --check
```

Python 3, NumPy and Numba are required. The offline bundle includes the exact source and MIT license, source hashes, fixed inputs, the unchanged pre-target `frozen-plan.json`, all observed scores and complete null winners. The producer's `--check` mode regenerates all numerical results without overwriting the archived outputs; it ignores only four explicitly named timing fields. Optional Walden and external-reference model inputs are not used by this constant-seed search; no replacement language model is introduced.
