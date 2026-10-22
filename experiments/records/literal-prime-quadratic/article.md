## What was tested

Suppose a rune is replaced by its Gematria Primus prime value: F becomes 2, U becomes 3, and so on through the 29-value alphabet ending at 109. Could one fixed quadratic formula rearrange that entire alphabet without producing any values outside it?

We tested `f(x) = ax² + bx + c (mod m)` for **every integer modulus m greater than 109**. A modulus sets the wraparound size: values that differ by a multiple of m count as the same output. We required the formula to send all 29 primes to **29 distinct primes from that same alphabet**. The result is identity only: under these assumptions, each prime must map back to itself.

This is a replication of the quadratic claim in the supplied research archive. The earlier scripts and reported result were inspected before the plan was written. It is not a new discovery or a blind test. A fresh enumerator and a separately implemented checker agree; human review remains pending.

This extends the [full-alphabet affine experiment](#/experiments/literal-prime-affine) by allowing an x² term. It does not rule out every arithmetic cipher. A changing key, a formula applied only to a page's observed runes, or an operation on rune **indices** rather than prime values asks a different question.

## Why an infinite range can be checked

Trying moduli up to a convenient maximum would leave every larger modulus unresolved. Instead, three chosen inputs restrict which moduli can work.

Call the prime alphabet S. The images of 2, 3 and 5 must be three different members of S; write them as u, v and w. There are `29 × 28 × 27 = 21,924` ordered choices. These three images determine the following integer expression:

```text
Q(x) = 2u(x−3)(x−5) − 3v(x−2)(x−5) + w(x−2)(x−3)
```

For any polynomial fitting those three images, `6f(x) ≡ Q(x) (mod m)`. The factor 6 matters: it cannot simply be cancelled when the modulus is divisible by 2 or 3.

For each choice of u, v and w, find the first alphabet value x for which Q(x) is not six times an alphabet value. If the final output is some y in S, then m must divide the **nonzero integer** `Q(x) − 6y`. A nonzero integer has only finitely many positive divisors. Taking the divisors for all 29 possible y therefore gives a complete finite list for this branch, including moduli larger than a guessed search cutoff.

The downloaded certificate records each branch's three images, the chosen witness x, its Q(x), and every candidate modulus. For each candidate the scripts recover all possible coefficients and check the entire output alphabet directly.

## The branch without a finite witness

Exactly one choice escapes that divisor reduction: `(u,v,w) = (2,3,5)`. In this branch Q(x) is exactly 6x as an integer, so a different argument is needed. All its possible maps have the form

```text
f(x) = x + a(x−2)(x−3) (mod m), with 6a ≡ 0 (mod m).
```

For every integer x, `(x−2)(x−3)` is either 0 or 2 modulo 6. The only possible changes from identity are therefore a shift by 2a; the input 7 already tests that shift. If it is nonzero, its circular distance from zero is m/3. But two members of this alphabet differ by at most `109−2 = 107`. A valid nonidentity map in this branch would consequently need `m ≤ 321`.

The checker directly scans the coefficient residues for all moduli 110 through 321. None gives a nonidentity permutation of the alphabet. The argument above handles every larger modulus; those larger moduli are not silently dropped.

## Results

| Finite branches | Candidate-modulus checks | Coefficient checks | Surviving maps |
| --- | ---: | ---: | ---: |
| Modulus coprime to 6 | 261,346 | 261,346 | 0 |
| Modulus divisible by 2 or 3 | 2,420,451 | 7,993,284 | 0 |

These counts are branch checks: a modulus can occur under several different choices of anchor images. They are not counts of distinct modulus values across the whole experiment.

The separate identity-anchor branch contains 318 coefficient expressions representing identity within the checked interval. **Different coefficients need not mean a different function.** For example, modulo 110,

```text
55x² + 56x = x + 55x(x+1) ≡ x.
```

The product x(x+1) is always even, so the extra term is divisible by 110. Reporting that quadratic coefficient as a nonidentity solution would be a mistake.

## Where the conclusion stops

The requirement to preserve the **whole** alphabet is essential. On only the three inputs `{2,3,5}`, the quadratic `22x² + 16x + 10 (mod 127)` swaps 2 and 3 and fixes 5. However, it sends 7 to 57, outside the prime alphabet. A smaller observed alphabet can therefore permit maps excluded by the full-alphabet test. See the [affine page-support variant](#/experiments/literal-prime-affine-pages) for a separate example of why page-level scope matters.

Injectivity is essential too: the constant function f(x)=2 always stays inside S, but destroys the distinctions between runes. Working with rune indices instead of their literal primes changes the domain. Higher-degree formulas, word-dependent operations, varying coefficients, and polynomial key sequences combined with unknown plaintext are also outside this experiment.

No candidate plaintext was scored. There was no selection of words that happened to look meaningful, and no claim about the language of the unsolved pages follows from this result.

## How to reproduce it

Use Python 3 with its standard library. No network service or model is needed. From the repository root, choose output filenames that do not already exist:

```sh
python -m unittest discover -s scripts -p test_quadratic_palette.py
python scripts/run_quadratic_palette.py --output quadratic-certificate.json
python scripts/check_quadratic_palette.py quadratic-certificate.json --receipt quadratic-audit.json
```

The first command compares both coefficient solvers against every coefficient triple for moduli 2 through 18, including cases where division by 6 is invalid. It also checks divisor generation and the scope counterexamples above.

The producer scans divisor pairs up to the square root and solves congruences using modular inverses after accounting for the greatest common divisor. The checker imports none of that code: it reconstructs divisors by prime factorization and obtains coefficient solutions by lifting a congruence to integer equations. It then checks every finite branch and the bounded identity branch against the saved certificate. The receipt identifies the certificate and checker by SHA-256.

Agreement between these implementations supports the computation. The all-modulus conclusion additionally depends on the reduction explained above. It has not been presented as a proof-assistant result or as completed human review.
