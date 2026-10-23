# What a missing doublet can—and cannot—tell us

## Finding

The joined rune stream for **LP2-00–55** has **86 equal adjacent pairs among 12,955 pairs**. The pinned [Round 18 filter analysis](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L2-filter-leak) considers an encryptor that avoids some repeated ciphertext runes by discarding a key draw and trying again. We checked the exact probability law behind that idea.

**If key symbols are independent and uniformly distributed**, every plaintext rune produces the same distribution of visible ciphertext runes after this filter. The unusually few repeats can reveal something about a *possible filter*, but the filter alone gives no clue about which plaintext rune produced an output. This does not show that LP2 uses such a key or that its text cannot be solved by other means.

![The same observed repeat rate can be produced by a skip filter that consumes roughly 374 extra key draws, or by a rewrite filter that consumes no extra key draws. The visible ciphertext law is identical under the stated independent uniform-key model.](experiments/records/rejection-channel-information/channel-comparison.svg)

## Why the same output can hide different mechanisms

Let the alphabet have 29 runes and let a candidate ciphertext rune be the plaintext rune plus a fresh uniform key symbol, modulo 29. A **skip filter** rejects a candidate matching the preceding output with probability *s* and draws another key symbol. Fitting its expected repeat rate to 86/12,955 gives *s* ≈ **0.8129**. The probability of a visible repeat is then `(1 − s)/(29 − s)`; each particular nonmatching rune has probability `1/(29 − s)`. Neither probability depends on the plaintext rune.

A different **rewrite filter** can match the same output law: when a candidate repeats, sometimes replace it with a new uniform rune. The fitted replacement probability is about **0.8363**. Here that replacement randomness is separate from the key stream. These mechanisms have the same visible one-step distribution. They differ in a testable way if an independent key stream is known: the skip model would consume about **374 extra key symbols** over 12,955 transitions on average, while the rewrite model would consume none. The source's fixed *s* = 0.8129 gives the same approximate drift; our exact calculation reproduces its preserved analytic mean.

This is a model comparison, not a claim that doublet suppression was actually performed. A key with structure, a plaintext-dependent filter, or a different reset rule changes the argument. The observed count was used to fit both models; it cannot independently validate either one.

## What was checked

The [plan](experiments/records/rejection-channel-information/plan.json) pins the source code and preserved numerical receipts. We re-derived the conditional probabilities, matched the source's closed repeat-rate and draw-count formulas, and checked both filters by independently enumerating every key, plaintext and previous-output combination in a nontrivial three-symbol control model. Zero suppression correctly returns a uniform output.

Run `python experiments/records/rejection-channel-information/run.py --check` and `python experiments/records/rejection-channel-information/check.py` from the repository root. The source's English-text entropy estimates and corpus-based simulations are **not reproduced** here because their exact corpora are not in the pinned source. Those estimates must not be read as a measured amount of LP2 plaintext leaked by the filter.
