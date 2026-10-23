# Do familiar number sequences unlock LP2's rune stream?

**Finding.** A published search through prime, Fibonacci, totient, polynomial, π-digit and related key streams reproduces exactly, but its best coincidence scores do not establish a decipherment. We replayed the source's whole-section candidate grid across nine LP2 sections. The strongest selected result, on pages 00–02, was matched or exceeded by 3 of 99 shuffled sections. Its plus-one tail is **4/100**; allowing for choosing among nine sections gives a simple bound of **36/100**. The other sections' conditional tails range from 7/100 to 88/100.

![Selected source-grid maxima compared with matched rune shuffles for each LP2 section.](experiments/records/leo-chain-sequence-keys/section-key-grid.svg)

This is an index-of-coincidence test. A higher score says the output symbol frequencies are less uniform under this one measure; it does not produce readable text or identify a key. The best of many keys needs to be compared with the **best** of the same many keys on controls. Two planted streams, one directly masked with a prime sequence and one encoded through the source's chain rule, cleared that full-grid control gate. No scanned LP2 section clears a nine-section selection comparison.

## What the source searched

[Leo's fourth test](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/tests4.py) defined 24 named integer streams, offsets 0–199 and both additive directions. It scored five views of each section: the original GP29 rune indices, Atbash, forward and reverse chain increments modulo 28, and forward chain increments tested modulo 29. Some names generate identical effective keys; the 500-element prime-index stream is too short for these section lengths. We retain all source names in the [complete result](experiments/records/leo-chain-sequence-keys/results.json) while reusing exact complement identities for the reverse-chain and Atbash scores. The saved top three candidates in all **45 section-and-view rows** match the pinned source receipt, as do all nine first-400-rune solved-text running-key rows.

The source's chain view turns a nonrepeating adjacent rune step into a number from 0 to 27; equal adjacent runes are omitted. This is a different question from directly subtracting a sequence from the original 29-symbol ciphertext. The result is limited to those exact representations, keys and offsets. It cannot rule out a different key source, sequence phase, boundary rule or a decoder scored by actual plaintext.

## Reproduce

Obtain [Leo's pinned repository](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/tree/a32bdc0e06ea58532fbaf4329acae4a0b1020513) with its generated `dataset.json`, and the [pinned relikd text](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4). The [plan](experiments/records/leo-chain-sequence-keys/plan.json) pins every input hash and the source grid. Substitute the two checkout paths below:

```text
python experiments/records/leo-chain-sequence-keys/run.py --source-root LEO --text-root RELIKD --check
python experiments/records/leo-chain-sequence-keys/check.py --source-root LEO --text-root RELIKD
```

The first command recomputes every source setting, planted control and selected-grid shuffle. The separate checker verifies the input bytes, all 135 printed top candidates, all nine solved-text key rows, planted-key recovery and the exact arithmetic symmetries. The pinned external source code and transcription are linked, not republished here.
