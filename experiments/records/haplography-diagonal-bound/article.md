## Finding

**A missed repeated rune cannot change the 28 nonzero difference counts tested here.** The source asks whether about 20 instances of *haplography*—writing a doubled rune once—could make a ciphertext-autokey pattern disappear from LP2. Restoring one duplicate changes `a → x → b` into `a → x → x → b`. The old `x → b` transition remains; only the new `x → x` transition is added. Its rune difference is zero.

![A duplicate insertion leaves the observed nonzero difference unevenness at 0.061. Even an artificial twenty-count allowance reaches only 0.066, compared with the source threshold of 0.40.](experiments/records/haplography-diagonal-bound/diagonal-bound.svg)

We reconstructed the source's **9,640 within-word adjacent pairs** from its pinned rune transcription and counted **60 equal-rune pairs**. The unevenness (coefficient of variation, or CV) of the 28 *nonzero* difference counts is **0.0608**. Inserting any number of exact adjacent duplicates leaves that number unchanged. This is an algebraic result, not a sampled search over insertion sites.

The source also gave a deliberately stronger, nonphysical adversary permission to add 20 counts to *any* nonzero difference. We independently bounded every such allocation: its largest possible CV is **0.0656**, still far below the source's **0.40** autokey-signal bar. At 40 additions the bound is **0.0717**. Our independent checker reconstructs the page runs by a separate parser, verifies all 41 bounds, and checks the insertion identity for every **29³** three-rune context.

## What the result means

For the specific relation `c[i] = p[i] + c[i−1] + K (mod 29)`, differences between consecutive ciphertext runes mirror plaintext-rune frequencies. A strongly uneven plaintext distribution would therefore produce uneven nonzero differences. Exact deletion or restoration of a duplicated ciphertext rune **cannot hide that particular difference pattern**. This says nothing about other feedback rules, other transcription errors, or a plaintext whose frequencies were already nearly flat.

The original source reports a positive control made from *Pride and Prejudice* rune frequencies, but its checkout does not include the `pride.txt` file that its script loads. We therefore **do not claim to reproduce its reported 0.842 control CV or 0.784 separation**. Our replacement control is explicitly synthetic and lumpy: a planted ciphertext-autokey stream scores **1.316** after 20 merges, while a uniform stream scores **0.050**. It checks that the statistic can distinguish those two constructed cases; it is not a model of every possible natural language.

The source's initially frozen no-error rule included `χ² < 40`. Its later addendum sets that clause aside because the artificial adversary crosses 40 while CV remains low. Our strongest conclusion—the exact physical-insertion invariance—does not depend on either threshold. The nonphysical 20-count comparison is reported against the source's unchanged CV bar, with that rule change visible in the bundled source documents.

## Reproduce

From the repository root, with Python 3 and no additional packages:

```text
python experiments/records/haplography-diagonal-bound/run.py
python experiments/records/haplography-diagonal-bound/check.py
python experiments/records/haplography-diagonal-bound/plot.py
```

The [result data](experiments/records/haplography-diagonal-bound/results.json), [pinned source transcription](experiments/records/haplography-diagonal-bound/source/krisyotam_runes.txt), and the source's original plan, code and report are bundled. The copied source is MIT-licensed. Our result covers the **single-rune duplicate insertion** mechanism and this one ciphertext-autokey diagnostic, not the whole autokey family.
