# Can a simple cipher imitate LP2's rare repeated runes?

A [published comparison](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/fingerprint.py) encrypts the same 2,979 runes of known Liber Primus text in 23 specified ways, then compares each output with the still-unread LP2 text. The measurements are repeated adjacent runes, overall rune balance, and matches two positions apart. We reproduced **all 23 rows** of its archived table from pinned inputs.

## Finding

![LP2's adjacent-repeat rate is 0.664%; the source's chain simulation is 0.672%. The match comes from the frequency of one plaintext rune.](experiments/records/leo-cipher-model-fingerprints/repeat-rate.svg)

LP2 has **86 identical adjacent pairs in 12,955 opportunities** (0.664%). One source simulation, `cipher = previous cipher + plaintext + 1` modulo 29, has **20 in 2,978** (0.672%). Its overall rune balance is also near uniform. These are real matches to the selected summaries, but they **do not identify LP2's encryption**.

The repeat-rate match has a simple explanation. Under that chain rule, a new cipher rune equals the previous one exactly when the plaintext rune is **EA**, index 28. EA occurs **20 times** after the first position in the chosen known reading. We verified that identity both algebraically and by generating and reversing the stream. The observation is therefore determined by this plaintext sample's rune frequency; the chain has not predicted a readable LP2 passage.

As an explicitly **post-observation** check, we held the same chain rule and plaintext fixed while trying all 29 additive constants. The source's `+1` is the closest of the 29 to LP2's observed repeat rate. That rank describes this particular chosen sample and one statistic; it is not a probability that the source cipher is correct. The [complete model and offset table](experiments/records/leo-cipher-model-fingerprints/results.json) preserves every value.

## What the comparison covers

The 23 rows include fixed-period keys, prime and Fibonacci streams, plaintext and ciphertext feedback, two running-key examples, affine substitution, random output, and several F-pass-through variants. The source generated **one** instance of each random-key model on the same 2,979-rune known reading. It compared those with 12,956 unread runes. This is a useful fingerprint demonstration, not a search over every key, every plaintext or every boundary rule.

One displayed source number needs care: it multiplies LP2's uniformity χ² by `2,979 / 12,956`, turning the actual **26.36** into **6.06** for its table. A chi-square statistic does not retain its original reference distribution after that scaling. We reproduce the printed value to audit the source, but do not use it to rank cipher models. The source's final “running key English with F-interrupts” row passes F unchanged while continuing to index the key by absolute position; it does not pause the key clock.

## Reproduce

Use [Leo's pinned source](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/tree/a32bdc0e06ea58532fbaf4329acae4a0b1020513) with its separately pinned [relikd input](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4) installed as that source expects. The scripts check the source, dataset, archived receipt and baseline file hashes. From the Liberpedia repository root, substitute the Leo checkout path for `LEO`:

```text
python experiments/records/leo-cipher-model-fingerprints/run.py --source-root LEO --check
python experiments/records/leo-cipher-model-fingerprints/check.py --source-root LEO
python experiments/records/leo-cipher-model-fingerprints/plot.py --check
```

The runner reconstructs the 23 outputs independently of the source implementation and compares all displayed rows with the saved receipt. The checker freshly runs the source script, compares its 23 rows again, tests the chain inverse, and independently verifies all 29 repeat-count identities. This record does not copy the source code or its third-party input texts.
