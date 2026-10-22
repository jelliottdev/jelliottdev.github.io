## Finding

The literal multiplicative ciphertext-autokey rule **cannot produce the archived LP2-00–55 stream**. With rune indices modulo 29, it says `c[i] = p[i] × c[i−1]`. Rune index **0 is F**. Once ciphertext reaches zero, multiplication keeps it zero whatever plaintext follows. Yet the transcription has **450 edges from F to a non-F rune**, spread across **all 55 nonempty pages**. One such edge is enough to contradict the uninterrupted rule.

![The archived stream has 458 index-zero runes and 450 zero-to-nonzero edges.](experiments/records/multiplicative-ciphertext-autokey/zero-state.svg)

This tests the proposed recurrence exactly as written, with a fresh page start but no exception inside a page. A rule that *skips* zero, resets the state, inserts a marker, changes the alphabet, or adds another term is a different proposal. It may avoid the contradiction, but needs an explicit encoder and decoder before it can be checked.

## Why doublets alone are insufficient

When the preceding ciphertext rune is nonzero, a repeated ciphertext rune under this recurrence means the plaintext rune at that step equals index **1**. That algebra can suggest a low doublet rate if index 1 is rare in the plaintext. It does not solve the zero-state problem. The saved result contains **82 nonzero doublets** and lists every zero-to-nonzero position, so the two observations can be checked separately.

The [additive-key doublet control](#/experiments/uniform-additive-doublets) and [single-rune deletion census](#/experiments/single-rune-null-doublets) examine different mechanisms; their findings should not be transferred to multiplication.

## Reproduce

From the repository root, using Python 3.12 and the standard library:

```text
python experiments/records/multiplicative-ciphertext-autokey/run.py --check
python experiments/records/multiplicative-ciphertext-autokey/check.py
```

The independent checker reads each transcription again and verifies the [saved position ledger](experiments/records/multiplicative-ciphertext-autokey/results.json). The producer also confirms the absorbing-zero rule on a short synthetic plaintext.
