# Can each rune label a divisor of its position?

**Not with consecutive positions, under the rule tested here.** Every nonempty rune page in LP2-00–55 contains repeated occurrences whose spacing makes a fixed divisor greater than one impossible, regardless of where counting starts. This is a fresh reproduction of the supplied closure archive's C11 claim, not an original discovery.

## Define the rule before testing it

Let i be a zero-based rune position within a page. Choose an integer origin N and a fixed stride s. Assign each rune r an integer divisor q[r] greater than one, then require:

```text
q[r] divides N + s*i whenever position i contains r
```

The same rune must keep the same divisor throughout that page. Divisors need not be prime, distinct, or equal to Gematria Primus values. Allowing all integers greater than one makes this test more permissive than an assignment restricted to primes. Each page may use its own origin, stride and assignment.

This is a necessary condition for a direct smallest-factor or largest-factor labeling proposal. It does not test prime-derived keys combined with plaintext or an arbitrary operation that merely uses prime numbers.

## Why the origin cancels

If q divides both N+s*i and N+s*j, it divides their difference s*(j−i). The unknown N disappears. For several occurrences, q must therefore divide the stride multiplied by the gcd of the position gaps.

For unit stride, a gap gcd of 1 would require q to divide 1. That contradicts q > 1. Running the page backwards changes the origin and stride sign, not this obstruction.

A rune appearing only once has no gap constraint. Two occurrences with gap 1 already suffice; otherwise several gaps may be needed. The report records every occurrence and, where available, a three-occurrence gcd-one witness. It uses gcd 0 for an empty set of gaps; that means no restriction from this particular test, not impossibility.

## A witness on LP2-00

F occurs at zero-based rune positions **7, 17 and 58**. Thus a fixed divisor must divide both 10 and 51 under unit stride. Their gcd is 1. This single repeated rune already rules out the model on that page; the report records the other rune labels as well.

These are positions in the filtered rune stream, including the heading. They are not image coordinates, Latin-letter offsets or positions that count punctuation.

## What the full retest covers

The program reads all 56 archived text files LP2-00–55, retains alphabet runes and headings, and starts each page independently. All **55 nonempty streams** have at least one gcd-one rune. LP2-50 has no alphabet runes in this transcription and is skipped; its alphanumeric grid is not converted into runes.

Every page therefore excludes both forward and reverse unit-stride constructions, even when the origin and arbitrary integer divisor labels are chosen independently for that page. This is an exact contradiction under the stated model, not a low probability or a finite search over origins.

## Why arbitrary strides remain different

With a gcd-one witness, the general condition is **q divides s**. It excludes a stride coprime to that rune's divisor. It does not exclude every nonunit stride.

For a concrete counterexample, set N=2, s=2 and q[r]=2 for every rune. Every position N+s*i is even, so every recorded rune passes the divisibility condition on every page. This construction assigns the same divisor to different runes, which the tested necessary condition permits. It supplies no decoding rule and does not identify which rune to emit at a position.

If a proposal requires distinct labels, literal GP primes, or a deterministic factor-selection rule, those extra requirements need separate analysis. The counterexample refutes the broader claim that this divisibility condition alone excludes all strides; it is not a successful cipher.

## Reproduce and independently check

Download the experiment ZIP and keep its folders intact. Python 3's standard library is sufficient; no network, AI calls or additional packages are needed.

```text
python experiments/records/position-divisor-labels/run.py --check
python experiments/records/position-divisor-labels/check.py
```

The first program uses distances from each rune's first occurrence. The independent checker reads page JSON and computes the gcd of all pairwise occurrence distances. It also verifies every displayed triple, the stride-two counterexample on all 55 pages, a valid unit-stride control, and 450 small synthetic origin/stride cases.

Both text sources share archival ancestry: agreement is a computation check, not an independent manuscript transcription review. The earlier archive cites a Lean proof; this package provides elementary reasoning and fresh integer checks, without claiming that the Lean development was rerun.

## Limits and reopening conditions

Changing which characters advance the clock, resetting within a page, changing a rune's divisor over time, selecting an irregular sequence of integers, or transforming the factor labels changes the model. Such proposals are not ruled out here. A transcription correction also requires a new run. This result belongs alongside other bounded exclusions, not under a heading claiming that prime-based ciphers are impossible.
