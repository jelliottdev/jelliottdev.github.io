## What was tested

Can one fixed rule `(a × p + b) mod m` rearrange all 29 Gematria Primus prime values into a different ordering of the same values? Here p is the literal prime, not a rune index. Every output must belong to the same prime alphabet, and distinct inputs must give distinct outputs.

For **every integer modulus m greater than 109**, the only resulting permutation is the identity: each prime stays itself. This is a fresh reconstruction of the supplied research archive’s C07 claim, not a new discovery or a rerun of its original certificate. No manuscript page or proposed plaintext is used.

## Results

| Check | Result |
| --- | --- |
| Distinct images of inputs 2 and 3 | 29 × 28 = 812 choices |
| Exact integer permutations without modular wrapping | One: a=1, b=0 |
| Remaining anchor choices | 811 |
| Candidate maps requiring modular checks | 13,212 |
| Nonidentity full-alphabet permutations | None |

This does not exclude shifts modulo 29 on **rune indices**, prime-derived running keys, or position-dependent transformations. It is specifically about a single affine map of the full literal-prime alphabet.

## Why the infinite range is finite to check

Let u be the output of 2 and v the output of 3. Subtract their congruences:

```text
2a + b ≡ u (mod m)
3a + b ≡ v (mod m)
a ≡ v − u (mod m)
b ≡ 3u − 2v (mod m)
```

No modular division is needed. Composite moduli and coefficients that are not invertible modulo m are included. For each u,v define the unreduced integer expression `L(p)=u+(p−2)(v−u)`.

If L sends every prime into the palette as ordinary integers, its nonzero slope makes it injective. Exhaustive anchor checking finds only L(p)=p in this branch. Otherwise choose a palette input p whose integer image L(p) is outside the palette. To obtain an allowed modular output y, **m must divide the nonzero integer L(p)−y**. Enumerating those divisors for all 29 possible targets gives every candidate modulus for that anchor pair.

The identity works for every m>109 because all primes are canonical residues. Every other branch has a nonzero divisibility witness, so it is finite. There is no unsearched large-modulus tail. The report lists every anchor, witness and candidate modulus.

## A worked branch

Suppose 2 maps to 3 and 3 maps to 5. Then L(p)=2p−1, so L(5)=9 is outside the palette. For any allowed output y from 2 through 109, the nonzero difference 9−y has absolute value at most 100. No modulus above 109 can divide it. This anchor pair therefore has no candidates.

Other pairs have larger differences and require checks. The program applies the reduction to every pair; this example alone is not the proof of the complete result.

## Where the conclusion stops

| Relaxed assumption | Counterexample | Consequence |
| --- | --- | --- |
| Drop injectivity | a=0, b=2, m=110 maps every prime to 2 | Output membership alone does not force identity |
| Use a partial palette | a=109, b=5, m=110 swaps 2 and 3 | The subset {2,3} has a nonidentity permutation |

The subset example is not a result about any actual manuscript page. A page using fewer than all 29 symbols requires its own support-specific test. Neither counterexample recovers plaintext.

## Reproduce

Extract the experiment bundle with its folders intact:

```text
python experiments/records/literal-prime-affine/run.py --check
python experiments/records/literal-prime-affine/check.py
```

Both commands use Python’s standard library and make no network or AI requests. The first reconstructs the full report. The second does not import the producer: it checks candidate completeness by scanning each witness’s bounded modulus range directly, then enumerates all coefficient pairs for moduli 110 through 125. Those sixteen controls check the implementation; coverage above them comes from the divisibility argument, not extrapolation. The checker also verifies the two counterexamples.

Both checks passed on 20 October 2026. The question, planned procedure and controls are in `plan.txt`. No search bounds, scoring rules or exceptions were changed after seeing the result. Source alphabet, scripts and output hashes are included in the record. Computational review is complete within this scope; human review is pending. No Lean or other proof-assistant build is claimed.

See [rune indices and prime values](#/wiki/rune-values), [prime indices](#/wiki/prime-indices), [cipher invariants](#/wiki/cipher-invariants), and [search space and bounds](#/wiki/search-space) before applying this result to another proposal.

The [completed page-support variant](#/experiments/literal-prime-affine-pages) checks the actual archived LP2 supports. It retains two additional LP2-55 maps, illustrating this distinction with manuscript data.
