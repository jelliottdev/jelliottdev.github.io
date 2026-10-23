# What can an entropy budget tell us?

A [published Round 18 calculation](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L2-filter-leak) counts bits in a proposed key-skip cipher and labels some key models “determined.” We replayed every number with the recovered exact source text. The arithmetic reproduces; the determinacy labels do **not** follow from it.

## Finding

![The source estimates 62.6 thousand ciphertext bits under a full random-pad model. The same output estimate is then reused for a 256-bit seeded key, whose English-plus-key input proxy is only 33.5 thousand bits. A deterministic model cannot have more output entropy than counted input entropy.](experiments/records/r18-entropy-budget-replay/budget-models.svg)

The source estimates **62,617 bits** of output entropy from a 29-rune filtered Markov model fitted to LP2's repeat rate. It separately measures **2.568 bits per rune** as the lowest test-set cross-entropy among six short Markov models of one King James Bible encoding, then scales that value to **33,269 bits** for a manuscript-length English proxy.

For a full independent random pad, its estimated input sum is about **98,025 bits**. Replacing the pad with a **256-bit seed** reduces that sum to about **33,525 bits**, but the source keeps the same **62,617-bit output estimate** and calls the negative difference “determined.” Those numbers cannot all describe one deterministic seeded-key model: output entropy cannot exceed the entropy of its inputs. A random rejection coin could supply additional randomness, but it must be counted explicitly, and the output law must be recalculated for that model. The source's 40-, 64-, and 32-bit seed rows have the same issue.

Even within one consistent model, an entropy difference is **not an if-and-only-if test for a unique plaintext**. The expression `H(P) + H(K) − H(C)` equals remaining *joint* uncertainty only with the requisite independence and deterministic-channel assumptions; positive joint uncertainty can coexist with a uniquely known plaintext, while a negative value signals incompatible assumptions. It does not certify a readable LP2 decryption.

## What the corpus measurement covers

The source encodes a fixed KJV text in Gematria Primus runes, trains Markov orders **0–5** on the first **400,000** runes, and scores the next **200,000**. Order **3** has the lowest measured cross-entropy on that test segment. Selecting the best order on the same test segment is a model-selection step, and one Bible segment is not a measured distribution for unknown LP2 plaintext. The source also simulates **1,000** constant-text and **1,000** English-text filters; their low adjacent-repeat rates are a control for the specified model, not a way to infer LP2's text.

The source's **323-bit** “filter information injection” is the reduction in *ciphertext entropy* under its fitted Markov law. It is not 323 bits about plaintext. The separate [exact conditional-channel result](#/experiments/rejection-channel-information) proves that, with independent uniform key draws and the stated filter, the visible next-rune law is identical for every plaintext rune. That proof has narrower assumptions than a claim about every possible LP2 cipher.

## Reproduce

The ZIP includes the exact [KJV input](exports/sources/gutenberg-10-kjv.txt), preserved from [Project Gutenberg](https://www.gutenberg.org/files/10/10-0.txt). The runner verifies its hash; the source-code checkout and NumPy are still required.

The [replay plan](experiments/records/r18-entropy-budget-replay/plan.json) pins revision `f08b20b`, every imported source file, the recovered KJV bytes, and the original output hash. It was frozen before our run after we inspected the published source. With that checkout at `SOURCE`:

```text
python experiments/records/r18-entropy-budget-replay/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --check
python experiments/records/r18-entropy-budget-replay/check.py
python experiments/records/r18-entropy-budget-replay/plot.py --check
```

The runner uses a temporary source tree and leaves the original checkout untouched. The [complete source output](experiments/records/r18-entropy-budget-replay/source-results.json) and [replay](experiments/records/r18-entropy-budget-replay/replayed-results.json) match in every field. The independent checker recomputes the entropy formulas and flags the model mismatch; it does not turn the KJV proxy into a claim about LP2's language or key.
