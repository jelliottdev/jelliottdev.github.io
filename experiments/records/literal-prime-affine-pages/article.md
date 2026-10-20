## What changes from the baseline?

The [baseline](#/experiments/literal-prime-affine) requires one affine map to permute the entire 29-prime alphabet. This variant uses the prime values actually present on each archived LP2-00–55 page. Outputs may be any of the 29 allowed primes, but distinct observed inputs must still have distinct outputs. A page may use its own fixed coefficients and modulus.

The modulus range remains **every integer m greater than 109**. We do not score English or select a proposed reading. The supplied archive’s C08 claim predicted two LP2-55 exceptions; the fresh calculation retained all survivors rather than filtering for that prediction.

## Results

| Archived page support | Pages | Candidate maps checked per distinct support | Nonidentity maps |
| --- | --- | --- | --- |
| All 29 prime values | 53 pages | 13,212 | None |
| 28 values, missing 7 | LP2-49 | 14,901 | None |
| 25 values, missing 7, 29, 59, 103 | LP2-55 | 14,901 | Two |
| No rune values | LP2-50 | Not tested | No conclusion |

Thus **54 of the 55 nonempty rune pages allow only identity** under this exact model. LP2-55 has two additional maps. LP2-50 contains the alphanumeric panel rather than a rune stream; this procedure does not interpret its characters as GP runes.

The counts refer to distinct input supports, not a separate rerun for each of the 53 identical full-support cases. There are 43,014 candidate-map checks across the three supports. The all-modulus identity branch is handled separately.

## The two LP2-55 exceptions

| Coefficients (a, b, m) | Image of prime 2 | Images of observed odd primes |
| --- | --- | --- |
| (58, 57, 114) | 59: rune label T | Unchanged |
| (102, 101, 202) | 103: rune label Y | Unchanged |

Both have the form `a=m/2+1`, `b=m/2`. For an odd prime p,

```text
ap+b = p + (m/2)(p+1) ≡ p (mod m)
```

because p+1 is even. At p=2, the result is `2+m/2`: 59 for m=114 and 103 for m=202. Each map therefore changes only F to T or Y on this page. It does not decode the remaining runes or recover word boundaries.

Neither 59 nor 103 occurs in LP2-55’s observed input support. Sending 2 to either value therefore does not collide with another observed input. On the full alphabet, the odd input 59 or 103 is fixed too, so two inputs would have the same output. That is why these exceptions do not contradict the baseline.

The coefficients 58 and 102 are not units modulo 114 and 202 respectively: each gcd is 2. Requiring the affine map to be invertible on the entire residue ring would discard them. Our stated model requires injectivity only on the observed prime support, so they must be retained.

## Complete enumeration without a modulus cutoff

Every nonempty page support contains primes 2 and 3. Assign distinct allowed images u and v to them, giving 812 anchor choices per support. These determine `a=v−u` and `b=3u−2v` modulo m.

For each pair, examine the unreduced expression `L(p)=u+(p−2)(v−u)` on the page’s support. If every integer output is already allowed, record that branch separately. In this dataset the only such branch is identity. Otherwise choose the first supported prime whose L(p) is outside the full palette. Every valid modulus must divide one of the nonzero differences `L(p)−y`, where y is an allowed target prime.

The script tests every resulting divisor above 109, requiring both allowed outputs and no collisions on the observed support. The complete report retains each anchor’s witness and candidate list, the two surviving maps and their full outputs, and every page’s source hash. There is no arbitrary upper modulus bound.

## Reproduce

Extract this variant’s bundle with its folders intact:

```text
python experiments/records/literal-prime-affine-pages/run.py --check
python experiments/records/literal-prime-affine-pages/check.py
```

Python’s standard library is sufficient. The bundle includes the baseline’s divisor helper and all 56 archived page texts. No network or AI requests are made.

The independent checker does not import the producer or divisor helper. It reconstructs page support by counting each alphabet symbol, verifies page hashes, enumerates the possible moduli directly within each witness’s mathematical bound, and checks every survivor. It also verifies that both LP2-55 exceptions fix all its odd input primes and move 2 to a previously absent value.

Both commands passed on 20 October 2026. The method and controls were recorded in `plan.txt`; no input boundaries, candidate criteria or modulus bounds were changed after inspecting the result. Human review is pending. This is an elementary calculation with a checked certificate, not a proof-assistant build or a new decipherment.

## Limits

The result concerns the archived rune transcription and one fixed literal-prime affine map per page. It does not cover corrected symbol streams that change a page’s support, position-dependent transformations, noninjective maps, nonlinear rules, rune indices modulo 29, or prime-derived keystreams. A change in any of those assumptions requires a separate variant.

See [rune values](#/wiki/rune-values), [the full-alphabet baseline](#/experiments/literal-prime-affine), and [search space and bounds](#/wiki/search-space) for the distinction between checking a model completely and claiming a general decryption.
