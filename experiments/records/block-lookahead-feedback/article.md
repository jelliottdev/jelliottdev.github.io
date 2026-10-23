# A block-start lookahead feedback rule

**Finding.** We made one posted block-feedback formula runnable by fixing its unspecified key to zero and its final lookahead to zero. Blocks of **five** and **seven** round-trip all 15 planted known-reading pages, so the decoder implements the declared rule. On LP2-00–55, neither block size reproduces any of the **15 fixed known 12-rune openings** at the start of any of the **55 nonempty pages** (825 comparisons per size). Its decoded rune distribution remains close to the raw manuscript's flat distribution. This is a result for the stated zero-key completion, not a rejection of the posted idea with an unknown key.

![At a block start, the ciphertext depends on a plaintext rune one block ahead. The decoded LP2 distribution remains close to raw LP2 and far from the solved LP1 reading control.](experiments/records/block-lookahead-feedback/lookahead-feedback.svg)

The source discussion proposed a way for ciphertext feedback to restart at regular boundaries. At ordinary positions, add the previous ciphertext rune; at a block start, add a plaintext rune one block ahead. In zero-based GP-29 indices, our fixed rule is:

```text
if i mod b != 0:  C[i] = P[i] + C[i-1]   (mod 29)
if i mod b == 0:  C[i] = P[i] + P[i+b]   (mod 29)
```

The source's formula also includes a key `k[i]`, but does not specify it. **We set `k[i] = 0` everywhere.** We start a block at each page's first rune, and set `P[i+b] = 0` only when the lookahead falls beyond that page. Those are declared choices needed to run the example, not historical facts about LP2.

## What the test shows

| Stream | Rune count | Index of coincidence | F runes |
| --- | ---: | ---: | ---: |
| Raw LP2-00–55 | 12,956 | 0.03448 | 458 |
| Decode with block size 5 | 12,956 | 0.03498 | 171 |
| Decode with block size 7 | 12,956 | 0.03509 | 142 |
| Documented LP1 readings, for context | 2,797 | 0.06114 | 44 |

The solved LP1 sample is a reference for the scale of a known reading, **not** a matched statistical null for every language or every LP2 section. The decoded output's index of coincidence and lack of fixed opening matches give no positive reading under this exact completion. Another key, phase, interruption rule or target plaintext is outside it. The source's reported synthetic size-five run used additional choices and cannot be reproduced from the supplied excerpt alone.

Decoding is direct: subtract the previous ciphertext rune at non-start positions. At the last block start, subtract the declared terminal zero; then work backward through block starts, subtracting the already recovered next block's first plaintext rune. This backward step is what distinguishes this experiment from ordinary lag-one feedback. The [complete report](experiments/records/block-lookahead-feedback/results.json) stores the first 24 decoded indices and a digest of **every full decoded page**, along with each positive-control result.

## Reproduce

The [plan](experiments/records/block-lookahead-feedback/plan.json) pins every LP2 transcription, the known-reading control file, both block sizes, and the missing-rule completions. Run from the repository root or extracted experiment ZIP with Python 3.12 or later:

```text
python experiments/records/block-lookahead-feedback/run.py --check
python experiments/records/block-lookahead-feedback/check.py
python experiments/records/block-lookahead-feedback/plot.py --check
```

The independent checker solves block-start equations as a chain of pair sums and checks all full-page digests. Both implementations recover all 15 known-reading inputs after encoding them. Neither chooses a key or a word after seeing LP2 output.
