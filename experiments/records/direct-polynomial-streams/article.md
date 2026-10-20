# Can a low-degree polynomial directly generate an LP2 page?

**No, under the exact model tested here.** Every nonempty rune page in archived LP2-00–55 fails a necessary condition for direct polynomial generation of degree at most eight, in both rune-index and prime-value coordinates. The obstruction applies to every integer modulus greater than one, not just a searched list of moduli.

This says nothing about a polynomial **key** added to unknown plaintext. In that model the polynomial generates only the key, while this test compares its output directly with the manuscript symbols.

## The proposed construction

Number the retained runes on one page i = 0, 1, 2, … . The tested rule is:

```text
c[i] ≡ P(N + s*i) (mod m)
```

Here P has integer coefficients and degree at most eight; N is any integer starting position; s is any fixed integer stride, including negative or zero; and m is any fixed integer greater than one. Coefficients, origin, stride and modulus may differ between pages. The output c[i] is either the rune's zero-based index or its literal Gematria Primus prime value. There is no additional alphabet mapping.

## Why differences can rule out infinitely many parameters

A forward difference subtracts each value from the next. For the squares 0, 1, 4, 9, 16, the first differences are 1, 3, 5, 7, the second differences are 2, 2, 2, and the third differences are 0, 0. Each difference lowers polynomial degree by at least one. A polynomial of degree at most d therefore has zero differences at order d+1.

Reducing a sequence modulo m may change those differences from zero into multiples of m. It cannot change the requirement that **m divides every difference at that order**. Consequently, m must divide their greatest common divisor (gcd). If that gcd is 1, no modulus m > 1 can work.

Substituting N+s*i into a polynomial does not increase its degree in i. This is why arbitrary origins and fixed strides are covered without enumerating them. The proof uses the algebraic form of the rule; it does not estimate a probability.

## A small example you can check by hand

| Sequence | Values | First differences | Second differences | Third differences |
| --- | --- | --- | --- | --- |
| Squares | 0, 1, 4, 9, 16 | 1, 3, 5, 7 | 2, 2, 2 | 0, 0 |
| Change only the last value | 0, 1, 4, 9, 17 | 1, 3, 5, 8 | 2, 2, 3 | 0, 1 |

The modified example has gcd(0, 1) = 1 at order three. It cannot be a quadratic polynomial stream modulo any m > 1 under the stated rule. A gcd other than 1 would merely leave possible divisors to investigate; it would not establish that a polynomial exists.

## Manuscript result and coverage

The retest uses the repository's archived rune text, retains headings, removes nonalphabet characters, and starts a separate stream for each page. Decimal labels, separators and line breaks do not advance the position. It tests degrees 1–8 separately; constant polynomials are included within every degree bound.

| Coverage | Count |
| --- | ---: |
| Page files LP2-00–55 | 56 |
| Nonempty rune streams | 55 |
| Representations per stream | 2 |
| Degree bounds per representation | 8 |
| Checks with gcd 1 | 880 of 880 |

LP2-50 contains no alphabet runes in this transcription and is explicitly skipped. Its alphanumeric grid is not converted into a rune stream. LP2-56 and LP2-57 are outside the scope.

For a concrete witness, LP2-00's zero-based rune indices have ninth differences beginning **−1078, 1882, −2478, 1805**. Their successive gcds are 1078, 2, 2, 1. Those four values alone exclude every modulus greater than one for degree at most eight. The downloadable ledger contains all differences and a short gcd-one prefix for each of the 880 checks.

## What would reopen the question?

A polynomial key mixed with plaintext, a higher-degree polynomial, irregularly skipped positions, internal resets, a different rune selection, or an additional output mapping changes the model. Those require their own tests. The result does not eliminate arithmetic ciphers, running keys, recurrences or periodic ciphers as general classes.

The result is tied to the supplied transcription, not to a new visual audit of every rune. If the transcription changes, rerun the calculation. Agreement between the text and page-JSON versions checks computation and packaging; those versions share their archival source.

## Reproduce and independently check

Extract the experiment ZIP with folders intact, or use the repository. Python 3's standard library is sufficient. No network requests, AI calls or additional packages are needed.

```text
python experiments/records/direct-polynomial-streams/run.py --check
python experiments/records/direct-polynomial-streams/check.py
```

The first command takes successive neighboring differences. The second reads page JSON and computes each difference directly with the binomial-coefficient formula, without importing the first implementation. It also checks 128 synthetic polynomial streams across degrees, moduli, origins and strides, plus the modified-square example above. Both commands must pass.

## Relationship to the earlier archive

This is a fresh reproduction of the supplied closure register's direct-polynomial claim (C10/C22), using the current published corpus. It is not an original discovery. The earlier archive describes formal Lean checks; this package supplies an elementary proof and independently checked integer calculations, and does not claim to rerun that Lean development. Other entries in the register are not certified by this experiment.
