# Do number sequences fit the rune-difference chain?

A [published test](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/tests5.py) asks whether LP2's **change from one rune to the next** follows a numerical key stream. It tries primes, Fibonacci numbers, π digits and other named sequences. Each nonzero rune change is mapped into one of 28 values; a repeated rune becomes a zero-change placeholder. The test allows two clocks: the placeholder either consumes a key value or it does not.

## Finding

![The strongest source-selected section score is near the median of 39 shuffled complete searches.](experiments/records/leo-chain-key-alignment/chain-key-control.svg)

Our full replay matches the source's printed best result in **all nine sections**. The largest is pages 54–55: a cubic-number key at offset 25, one discrete-log mapping and the consume-at-doublets clock gives normalized coincidence **1.146**. That value is the best after searching **352,800 settings for this section**. Repeating the *entire* grid on 39 shuffled versions of the same section produced a median best of **1.147**; **20 of 39** matched or exceeded 1.146. This comparison was made on the section highlighted by the source printout, so it is conditional on that earlier selection. The reported best does not stand out under this control.

The source's planted controls work. We encoded a known 1,500-rune passage with a prime-number chain and tested both key-clock conventions. Each full-grid search recovered the planted family and clock, scoring **1.663**. The offset is 51 rather than the encryption start of 50 because the scan begins with the *second* ciphertext rune's change. That control shows the search can recover this particular synthetic construction; it does not mean every chain cipher would produce an equally strong signal.

## What was searched

The [frozen plan](experiments/records/leo-chain-key-alignment/plan.json) gives the source's nine section files, sequence generators, 14 mappings of nonzero changes, 300 key offsets, two signs and two placeholder clocks. The source names 23 sequences, but its own length gate skips **emirps and twin primes** in this window; 21 are evaluated. Its `primeidx` stream duplicates `prime` and is retained for faithful replay, not counted as a separate idea. The [results](experiments/records/leo-chain-key-alignment/results.json) list each section's best setting and the strongest setting for each eligible sequence. This is one method family with many parameter settings, not hundreds of independent experiments.

The [independent checker](experiments/records/leo-chain-key-alignment/check.py) recalculates each selected score with scalar arithmetic, verifies the nine rounded source-receipt values and confirms both planted encryptions. The complete-grid runner also reproduces all 39 shuffle maxima. The graphic shows the conditional comparison for pages 54–55.

Coincidence measures repeated values, not intelligible plaintext. This experiment does not decrypt a page, score language, test other source inputs or rule out sequence-derived ciphers with different mappings, clocks or boundaries. The 39-shuffle control is a modest conditional reference, not a universal probability for every numerical idea.

## Reproduce

Use the pinned [Leo source checkout](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/tree/a32bdc0e06ea58532fbaf4329acae4a0b1020513) at `LEO`, with its separately pinned [relikd transcription](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4) in the source's `sources/relikd_LiberPrayground` directory. The scripts verify source, π, baseline and section hashes before computing:

```text
python experiments/records/leo-chain-key-alignment/run.py --source-root LEO --check
python experiments/records/leo-chain-key-alignment/check.py --source-root LEO
python experiments/records/leo-chain-key-alignment/plot.py --check
```

The full search uses NumPy and Numba; the independent checker uses Python's standard library. This record describes the source method without copying its implementation.
