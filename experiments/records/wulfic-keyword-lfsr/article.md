# A keyword that feeds a shifting register

The archived [advanced cipher program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/advanced_cipher_solver.py) tries a keyword-seeded *linear feedback shift register* on ten manuscript pages. **None of its 400 settings crossed the program's reporting cutoff** on LP2-04–13. The best normalized coincidence value on any page was **1.10**, below the required **greater than 1.20**. This is a result for the source's fixed keywords and register rules, not for every feedback cipher.

![Each page's highest normalized coincidence value is below the source gate of 1.20; a known-reading control reached 2.06.](experiments/records/wulfic-keyword-lfsr/comparison.svg)

The keyword gives the first register values. At each rune, the register emits its first value as the key, then calculates a new value from selected positions before shifting. With `CABAL` as `5, 24, 17, 24, 20` and taps at zero-based positions 1 and 4, the key starts `5, 24, 17, 24, 20, 15…`; the new value `15` is `(24 + 20) mod 29`. The program tries register lengths **4–8**, four tap lists at each length, and two directions of subtraction. Each page starts its own register.

We tested the reporting rule on a full message first. A **209-rune established reading** was encrypted with one of the declared CABAL settings. The same 400-case search recovered every rune, cleared the coincidence cutoff at **2.06**, and ranked the correct case first. This shows that the gate can find a clean in-family message. It does not prove the gate would catch a noisy, interrupted, differently encoded, or layered message.

The archived page files 21–30 match the current LP2-04–13 rune arrays exactly. The 400 source settings yielded **396 distinct decoded outputs**, because four pairs of settings coincide on particular pages; they are still one method family. The source reports and English-substring-scores an output only after its whole-page normalized `29 × IoC` exceeds 1.20. **Zero** manuscript outputs cleared that rule. In **199** complete searches over independently shuffled pages, zero outputs cleared it there too. With no reported scores on either side, the shuffles do not provide a useful score-ranking or significance claim. They only show that this cutoff is stringent for these page lengths and frequencies.

The [plan](experiments/records/wulfic-keyword-lfsr/plan.json) fixes the ten pages, 400 settings, full-message control and whole-search shuffle procedure. The [results](experiments/records/wulfic-keyword-lfsr/results.json) retain the coincidence measurement and decoded-output digest for every setting; the separate [control result](experiments/records/wulfic-keyword-lfsr/control-results.json) was written before the manuscript scan. The related [keyword-ramp](#/experiments/wulfic-keyword-ramp) and [crib-inferred recurrence](#/experiments/wulfic-crib-lfsr-recurrence) tests use different key clocks.

From the full checkout or experiment bundle, supply an exact checkout of the pinned public Wulfic revision separately:

```text
python experiments/records/wulfic-keyword-lfsr/run.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT --check
python experiments/records/wulfic-keyword-lfsr/check.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT
python experiments/records/wulfic-keyword-lfsr/plot.py --check
```

The source checkout does not provide a license, so its script is not copied into the bundle. The runner imports only the SHA-256-verified Git blob. The independent checker rebuilds the register, both decryption directions, all 400 outputs, the planted reading and all 199 shuffled searches without importing the producer.
