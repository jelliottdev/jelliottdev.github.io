## Finding

Three similar-looking feedback rules make different predictions. For **additive** feedback, `c[i] = p[i] + c[i−1]`, a ciphertext doublet requires `p[i] = 0`. For **Beaufort-style** feedback, `c[i] = c[i−1] − p[i]`, the same is true. Their literal inverse outputs are negatives of each other modulo 29, so they identify **exactly the same 86 zero positions** in LP2-00–55. Doublet placement alone cannot distinguish these two rules.

For the **subtractive** variant, `c[i] = p[i] − c[i−1]`, the inverse is `p[i] = c[i] + c[i−1]`. Its zero condition is a pair summing to zero, not a repeated pair. The archived stream yields **437 zero outputs** under that literal inverse, rather than 86.

![Zero-output counts for additive, Beaufort and subtractive feedback.](experiments/records/linear-ciphertext-feedback/zero-outputs.svg)

These are structural statements about precisely written recurrences. Neither 86 nor 437 tells us that the corresponding inverse is readable plaintext. A key term, symbol remapping, zero skip, or interrupted clock would change the model. The [literal multiplication check](#/experiments/multiplicative-ciphertext-autokey) addresses another feedback rule with a stronger, absorbing-zero contradiction.

## Reproduce

Python 3.12 standard library, from the repository root:

```text
python experiments/records/linear-ciphertext-feedback/run.py --check
python experiments/records/linear-ciphertext-feedback/check.py
```

The first command rebuilds the [29-bin output frequencies](experiments/records/linear-ciphertext-feedback/results.json), page-by-page zero counts and figure. The second independently recounts the three zero conditions from each transcription and checks the modular identity.
