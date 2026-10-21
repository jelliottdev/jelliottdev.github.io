# Full-palette quadratic maps: replication scope

This follows the published affine-map experiment within the same literal-prime family. The supplied archive already claims that only the identity function survives. Its two scripts and reports were inspected before this design. This is a replication with fresh enumeration and independent controls, not a new discovery or a blind test.

## Exact question

Let S be the 29 stored Gematria Primus prime values, from 2 to 109. For every integer modulus m > 109 and every integer-coefficient polynomial f(x) = ax² + bx + c, does the set of outputs on S equal S? Equality of these 29-element sets includes injectivity on S. Coefficients are residues modulo m, but the conclusion concerns the resulting function on S, not uniqueness of its coefficient expression.

Do not expand this to partial page supports, ordinal alphabets, noninjective maps, higher degree, position-dependent rules or polynomial keystreams mixed with unknown plaintext. Those have different domains or equations.

## Reduction from infinitely many moduli

An injective map assigns distinct images u, v, w in S to anchors 2, 3, 5. Enumerate all 29×28×27 anchor triples. Define

`Q(x) = 2u(x−3)(x−5) − 3v(x−2)(x−5) + w(x−2)(x−3)`.

For any candidate polynomial, Q(x) is congruent to 6f(x) modulo m. When an input x has Q(x) outside the integer set 6S, every valid modulus must divide one of the nonzero integers Q(x)−6y, y in S. Enumerate their positive divisors above 109. This finite-divisor step is necessary even when 6 is not invertible modulo m; dividing by 6 without checking its gcd would lose valid coefficient candidates.

For each candidate modulus solve `6a ≡ 2u−3v+w (mod m)`. With g = gcd(6,m), there are no solutions unless g divides the right side; otherwise enumerate all g residue solutions. Recover b and c from the two remaining anchor equations and check all 29 outputs directly. Keep branches with every exact Q(x) in 6S separate rather than discarding them.

If the only exact-image branch is (u,v,w) = (2,3,5), the remaining form is `f(x) = x + a(x−2)(x−3)` with `6a ≡ 0`. The product is 0 or 2 modulo 6, so any nonidentity behavior is already visible at x=7. The nonzero output shift has magnitude at least m/3 modulo m. Two palette values differ by at most 107, so nonidentity behavior in this branch requires m ≤ 321. Verify that finite interval and explain why larger moduli cannot add a nonidentity map. If additional exact-image branches occur, stop and analyze them; do not claim all-modulus closure from this argument.

## Evidence and controls required

Save every anchor's witness and candidate-modulus list, candidate and coefficient totals, all surviving maps, and the exact-image branches. Partition counts by gcd(m,6)=1 versus gcd(m,6)>1 for comparison with the earlier two-part result. Keep the enumeration deterministic.

Independently verify the coefficient solver by brute-force small-modulus coefficients, including singular moduli. Independently reconstruct the divisor certificate with a different factorization/enumeration method and direct polynomial evaluation. Check the bounded exact-image branch and distinguish functional identity from coefficient aliases.

Preserve explicit counterexamples: constant output 2 when injectivity is removed; a quadratic swapping 2 and 3 while fixing 5 on a proper subset at modulus 127; and a nontrivial coefficient expression that acts identically. A diagram should show the anchor, finite-divisor and exact-image branches so a reader can understand why the result covers all m rather than an arbitrary cutoff.

The earlier reported outcome is not assumed in the producer. Any conflicting survivor is retained and investigated. No proof-assistant rerun or human review is claimed.
