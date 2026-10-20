# Totients of consecutive integers

“Try the totient function” leaves an important choice unresolved: the totients of which numbers? This experiment uses consecutive positive integers, beginning with φ(1), rather than consecutive primes.

All 3190 planned page/offset/direction configurations completed and produced 3190 distinct page outputs. None began with one of the nine declared 12-rune openings. This is an exact-opening result, not an assessment of general readability.

## What changes from the baseline?

The [prime-minus-one baseline](#/experiments/lp2-prime-minus-one-openings) applies the sequence 1, 2, 4, 6, 10… derived from successive primes. This variant changes only that schedule:

```text
Input integer:  1  2  3  4  5  6  7  8  9 10
Totient:        1  1  2  2  4  2  6  4  6  4
```

The totient φ(n) counts integers k from 1 through n whose greatest common divisor with n is 1. Thus φ(8) = 4 because 1, 3, 5 and 7 qualify. For n = 9, the six qualifying integers are 1, 2, 4, 5, 7 and 8. They do not all have to be prime; they must be coprime to the chosen n. The convention φ(1) = 1 is included.

For a prime p, every integer from 1 through p−1 is coprime to p. Therefore φ(p) = p−1. Applying φ to consecutive primes would reproduce the baseline schedule and is not a separate experiment under otherwise identical rules.

See the [totient guide](#/wiki/totient) for the definition, factorization formula and connection to the known LP2-56 recipe.

## Exact transformation

For rune position j, starting offset s and direction d:

```text
output[j] = (input[j] + d × φ(j+s+1)) mod 29
d = −1 for subtraction, +1 for addition
```

Positions and offsets are zero-based. Offset zero starts at φ(1); offset one starts at φ(2). Both start with the value 1, but their later terms differ. A matching first value does not make two schedules identical.

| Setting | Declared choice |
| --- | --- |
| Pages | LP2-00–55; LP2-50 has no recognized runes and contributes no candidates |
| Input | All archived runes in order, including headings |
| Starting offsets | Every integer 0–28, selecting initial inputs 1–29 |
| Arithmetic | Addition and subtraction modulo 29 |
| Advancement | One term per recognized rune; non-rune characters consume no terms |
| Boundaries | Reset at each page, not at words or rows; no interruptions |
| Acceptance | Exact first-12-index match to a declared known opening |

Each of the 55 nonempty pages has 58 configurations, for 3190 in total. The complete output tuple is retained for every configuration. Checking those tuples found no repeated outputs within a page in this particular bounded search. That observation is not a proof that arbitrary later totient offsets must all differ.

## The opening criterion

The references are the first 12 output indices from Warning, Welcome, Some Wisdom, the first koan, Loss of Divinity, the second koan, Instruction, LP2-56 and LP2-57. Their vectors and source-trace hashes are fixed in the plan.

There were 28,710 exact comparisons and zero matches. The code does not reward partial words or rank how English-like a candidate appears. A valid plaintext with a different beginning would fail this criterion.

## Controls and retest

The plan and runner were committed as c84258a before execution. No input conventions, offset bounds or acceptance rules changed after inspecting the search results.

The runner uses a totient sieve: it starts with each integer n and removes the fraction divisible by each distinct prime factor. The separate checker takes a deliberately different route, calculating gcd(k,n) for every k from 1 through n and counting the ones. It verifies every generated totient needed by the search, not just the small examples.

A hand arithmetic control subtracts 1, 1, 2, 2 from indices 25, 11, 22, 15 to obtain 24, 10, 20, 13 modulo 29. This is not presented as a known reading. The checker then verifies all candidate outputs by undoing their arithmetic, checks the complete configuration set, audits the opening vectors against their source CSVs, and counts distinct page outputs. A full second execution reproduces the saved JSON exactly.

Review is computational; human review remains pending.

## Reproduce

From the repository root, with Python 3.12:

```sh
python experiments/records/lp2-totient-openings/run.py --check
python experiments/records/lp2-totient-openings/check.py
```

To save a fresh result at a path that does not already exist:

```sh
python experiments/records/lp2-totient-openings/run.py --output totient-rerun.json
```

The scripts use the standard library and local files, without network or model calls. The result stores the applied totient sequence, page lengths, all complete candidates and their match decisions.

## What this leaves open

Later offsets, different beginnings, interruptions, heading removal, transposition and combined transformations remain outside the test. Applying φ directly to rune values, prime sums or another derived input would also be a different procedure.

The manuscript’s reference to the totient makes it a reasonable function to examine; it does not determine those choices. A future record should state its inputs as precisely as its formula. This family now documents prime-minus-one, ordinary primes, Fibonacci and consecutive-integer totients under a common narrow opening criterion; it does not exhaust numerical ciphers.
