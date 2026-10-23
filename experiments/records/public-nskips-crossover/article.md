# How much text does a skip-count test need?

One proposed cipher model sometimes advances the key without consuming a manuscript rune. Its exact decoder permits such a skip only when the skipped key position would reproduce the previous ciphertext rune. A decoder can count those extra advances. This [published experiment](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round21/L2-nskips-crossover-length/RESULTS.md) asks when that count can distinguish a **deliberately planted message and its correct key** from random ciphertext paired with random keys. It tests the measuring tool; it does not decode an unsolved page.

## Finding

For the source's exact `keyskip1` decoder, the planted key first clears its **1% two-sided comparison bar at 6,000 runes**. It does not clear the bar at the preceding measured length, 3,600, and it still clears it at 9,000 and 12,956. Thus the observed crossing lies in **(3,600, 6,000]**, on this ten-point length ladder. This is a bound for this plant and this null model, not a universal minimum length or evidence that LP2 uses the modeled cipher.

![The planted correct-key skip count crosses the wrong-key upper-tail threshold at 6,000 runes, then remains above it.](experiments/records/public-nskips-crossover/crossover.svg)

At 3,600 runes the correct-key path made **94 skips**; the 1% upper-tail threshold of the 300 wrong-key trials was **107**. At 6,000, the correct path made **198**, above a threshold of **176**. The planted plaintext was recovered with at least **99.8% agreement** at every length, so a failed comparison below 6,000 was not caused by a decoder that could not recover its own test message. A reported two-sided value of `0.000` means none of the 300 sampled null trials was as extreme; it is not a zero probability.

## What was tested

The source planted one message at each of **400, 600, 900, 1,200, 1,600, 2,400, 3,600, 6,000, 9,000 and 12,956 runes**, using its fixed skip rule and seed 3301. For each length and decoder mode it compared the correct-key skip count with 300 uniform-random ciphertext and key pairs of the same length. Its criterion required both a two-sided empirical value at or below **0.01** and at least **90%** recovery of the planted message. The two endpoints were checked first: 400 did not separate, while 12,956 did. The source does not cap its doubled-tail statistic at one, so its reported `1.04` at 600 runes is not a probability.

The archive contains **34 reported cells**. Ten lengths were measured for the exact decoder and for a more permissive drift decoder, and a separate ten-length curve planted a `skip_by_two` mechanism. Four additional labels were measured at the 6,000-rune point. Those labels do **not** represent different language corpora in the executable: the plant uses English *Self-Reliance* text for all of them and changes the chosen window with the label. The script also promised an order-preserving shuffle surrogate in its plan, but only the random ciphertext/key null is executed here.

The alternate channels illustrate why a numerical separation cannot stand alone. The permissive drift decoder produces many spurious skips with random keys, so the correct key falls in its **left** tail even at short lengths; that is a different effect from the excess-skip footprint in the exact decoder. The `skip_by_two` plant never reaches the required recovery floor, so its curve cannot establish a crossover for that mechanism. Neither channel should be combined with the exact-channel crossing.

These are **single planted messages per length**, not repeated estimates of how often the method succeeds on arbitrary messages. No LP2 keys were searched, no plaintext language was inferred, and the numerical bound changes if the plant, null, decoder or threshold changes. In particular, this test does not rule out a useful shorter-window statistic or a different skip rule.

## Reproduce

The bundled [result data](experiments/records/public-nskips-crossover/source/liber-primus/analysis/round21/L2-nskips-crossover-length/nskips_crossover.json) retains every discrete null histogram. The [independent checker](experiments/records/public-nskips-crossover/check.py) recomputes the reported thresholds, tails, crossing and endpoint gate, then compares the replay with the pinned source result. From a Liberpedia checkout:

```bash
python experiments/records/public-nskips-crossover/check.py
python experiments/records/public-nskips-crossover/run.py
```

The full runner copies the source to a temporary folder. It reuses a null sample when multiple cells call the source with the **same length, decoder mode, seed and 300-trial input rule**; the source would otherwise recompute identical samples. Every resulting cell is checked against the pinned output. For the exact executable, input files and predeclared rules, inspect the [source driver](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round21/L2-nskips-crossover-length/crossover.py), [plan](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round21/L2-nskips-crossover-length/PREREG.md), and [bundled source files](experiments/records/public-nskips-crossover/source/liber-primus/analysis/round21/L2-nskips-crossover-length/PREREG.md).
