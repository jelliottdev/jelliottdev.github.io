# What changes if we use primes instead?

This is a single-variable follow-up to the [prime-minus-one baseline](#/experiments/lp2-prime-minus-one-openings). It replaces the sequence 1, 2, 4, 6, 10… with 2, 3, 5, 7, 11… and leaves the page selection, starting offsets, arithmetic directions, advancement and match rule unchanged.

All 3190 candidates completed. None began with one of the nine fixed 12-rune openings. The result is limited to that opening rule; the script does not decide whether a candidate is meaningful text.

## Why compare these two?

The [known LP2-56 recipe](#/wiki/prime-minus-one) uses primes minus one. Trying ordinary primes is an understandable next step, but it is useful to know exactly how much it changes.

Let c be an input rune index, p the next prime, and d the direction: +1 for addition or −1 for subtraction. Both outputs are reduced modulo 29.

```text
baseline = c + d × (p − 1)
variant  = c + d × p

variant − baseline = d
```

With subtraction, every variant output is one alphabet position below the corresponding baseline output. With addition, every output is one position above. This relationship holds at every rune and every tested starting offset. It does not depend on whether the text has a meaningful reading.

The checker verifies that relationship for every saved output, as well as checking the prime arithmetic independently.

## What stayed fixed?

| Setting | Both experiments |
| --- | --- |
| Pages | LP2-00–55; the nonrunic LP2-50 contributes no candidates |
| Representation | All archived runes, including headings, in source order |
| Starting offsets | 0–28 inclusive; zero starts at prime 2 |
| Directions | Addition and subtraction modulo 29 |
| Advancement | One term per rune, without interruptions |
| Reset | Restart the sequence on each page; not at rows or words |
| Criterion | First 12 output indices exactly match one of nine fixed openings |

The nine openings are Warning, Welcome, Some Wisdom, the first koan, Loss of Divinity, the second koan, Instruction, LP2-56 and LP2-57. Their vectors and source hashes are preserved in the plan.

This is 55 rune-bearing pages × 29 offsets × two directions = 3190 full candidates, each compared with nine openings: 28,710 comparisons. The bound of 29 offsets does not cover every possible starting point in a nonrepeating sequence.

## What the result means

Neither schedule produced one of the declared beginnings within these bounds. The two results are related, not independent statistical confirmations. There is no probability calculation or language score here.

For an exact opening criterion, a one-position difference matters: an output can match a fixed opening while its shifted counterpart does not. For a search that already tries all 29 constant shifts after decoding, however, the two schedules cover the same set of outputs. Adding one to a shift merely chooses another member of that same set. Such a search should not count these schedules as independent extra coverage.

The constant-shift equivalence assumes identical input, offsets and advancement. It does not automatically apply when one version skips a rune and the other consumes a key term.

## Controls and review

A hand calculation checks that input indices 25, 11, 22, 15 minus primes 2, 3, 5, 7 give 23, 8, 17, 8 modulo 29. This is an arithmetic control, not a claimed plaintext. The baseline's known LP2-56 control establishes the prime-minus-one reading separately.

The plan and runner were committed as e897c97 before this variant ran. The baseline result was already known; this is explicitly a follow-up, not a blinded independent test. No scope or acceptance rule changed after the variant result was inspected.

A complete rerun matches the saved result exactly. The independent checker generates primes by trial division rather than the runner's sieve, verifies every candidate through inverse arithmetic, checks the complete set of page/offset/direction cases, verifies each opening against its CSV, and compares every output with its baseline counterpart. Review is computational; human review remains pending.

## Reproduce it

From the repository root, with Python 3.12:

```sh
python experiments/records/lp2-prime-openings/run.py --check
python experiments/records/lp2-prime-openings/check.py
```

To save a fresh result at a new path:

```sh
python experiments/records/lp2-prime-openings/run.py --output prime-rerun.json
```

The scripts use the standard library and local files. Every candidate retains its complete output indices, page, offset, direction and matching-opening list. The checker also requires the baseline's frozen plan and results, which are included in the repository and reference-data download.

## Remaining questions

Other starting offsets, different beginnings, interruptions, reversed input and different boundary rules remain outside this search. Fibonacci and totient schedules would be distinct variants, not conclusions implied by this one. A broader plaintext score would need documented controls and a clear interpretation before its rankings could support a claim.
