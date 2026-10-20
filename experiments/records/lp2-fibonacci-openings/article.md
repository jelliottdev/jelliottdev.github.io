# Fibonacci shifts and known openings

This variant replaces the prime-minus-one schedule with Fibonacci numbers while preserving the baseline's pages, offsets, arithmetic directions, advancement and exact-opening rule. It has its own result page because changing a sequence is a different test, even when the surrounding procedure stays fixed.

All 3190 planned configurations completed. They produced **1540 distinct page outputs**, none of which matched one of the nine declared 12-rune openings. The distinction between configurations and outputs matters: many starting offsets repeat the same transformation.

## Define the sequence before using it

This test uses F_0 = 0, F_1 = 1, and each subsequent term is the sum of the previous two:

```text
0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...
```

For input rune index c at position j, starting offset s, and direction d:

```text
output[j] = (c + d × F_(j+s)) mod 29
d = −1 for subtraction, +1 for addition
```

Offset zero starts with 0, 1, 1, 2. Offset one starts with 1, 1, 2, 3. Stating the initial terms avoids the ambiguity between conventions that begin the written list with 0, 1 or 1, 1.

The input is the full archived rune stream, including headings. Every recognized rune consumes one term. Non-rune characters do not. The schedule restarts at each page and does not restart at a word or row.

## Why 29 starting offsets do not mean 29 different phases

Only the remainder modulo 29 affects an output rune. The first 14 Fibonacci remainders are:

```text
0, 1, 1, 2, 3, 5, 8, 13, 21, 5, 26, 2, 28, 1
```

The next two remainders are 0 and 1, the starting pair. A single repeated value would not be enough to establish a cycle: the recurrence needs two successive values. Once the pair repeats, all later values follow the same recurrence and repeat too.

The checker verifies that no earlier pair equals the initial pair. The exact period is therefore 14 for this sequence modulo 29. Offsets 0, 14 and 28 are equivalent; offsets 1 and 15 are equivalent; and so on.

The offset range 0–28 was retained to isolate the schedule change from the [prime-minus-one baseline](#/experiments/lp2-prime-minus-one-openings). It already includes every phase of this Fibonacci residue cycle. Larger starting offsets cannot add outputs under these same rules. That conclusion would need reconsideration if a proposed method used unreduced term values to control some additional operation.

## What was compared

| Item | Scope |
| --- | --- |
| Pages | LP2-00–55; LP2-50 has no recognized runes and contributes no candidates |
| Offsets | Every integer 0–28 |
| Directions | Addition and subtraction |
| Boundaries | Page reset; uninterrupted rune-by-rune advancement |
| Match | First 12 output indices equal a fixed known opening |
| Configurations | 55 nonempty pages × 29 offsets × two directions = 3190 |
| Distinct page outputs | 1540, counted by comparing complete output tuples within each page |

Each output was compared with the openings of Warning, Welcome, Some Wisdom, the first koan, Loss of Divinity, the second koan, Instruction, LP2-56 and LP2-57. The plan stores the exact vectors and their source-trace hashes.

The nominal configuration count gives 28,710 comparisons; after removing duplicate page outputs there are 13,860. Neither figure is a count of statistically independent observations. There is no significance test or general English score here.

## Result and its limits

There were zero exact opening matches. Every complete candidate remains available in the saved result, including the repetitions needed to compare with the declared offset range.

This excludes only the nine chosen beginnings under the stated transformation. A genuine reading beginning differently would not match. Interruptions, heading removal, reversals, altered Fibonacci seeds, additional constant shifts and combinations with another cipher were not tested.

The sequence is being tested as a conventional candidate idea. This record does not identify a manuscript instruction requiring Fibonacci numbers or establish them as an intended key.

## Controls and retest

The plan and runner were committed as 3c9a990 before the page search ran. The residue-cycle calculation was checked while specifying the plan, without examining candidate page outputs. No scope or acceptance rule changed after the search.

A hand control subtracts 0, 1, 1, 2 from indices 25, 11, 22, 15, producing 25, 10, 21, 13 modulo 29. This checks arithmetic; it is not a known plaintext.

The runner generates Fibonacci integers by repeated addition. The separate checker uses fast doubling:

```text
Given a = F_k and b = F_(k+1):
F_(2k)   = a × (2b − a)
F_(2k+1) = a² + b²
```

It verifies every saved term and candidate through inverse arithmetic, audits the complete configuration set, checks the reference openings against their source CSVs, and verifies every offset against its equivalent offset modulo 14. It also counts distinct full output tuples independently. A complete second execution reproduces the saved result exactly. Human review remains pending.

## Reproduce

From the repository root with Python 3.12:

```sh
python experiments/records/lp2-fibonacci-openings/run.py --check
python experiments/records/lp2-fibonacci-openings/check.py
```

To save a fresh result without replacing the reviewed output:

```sh
python experiments/records/lp2-fibonacci-openings/run.py --output fibonacci-rerun.json
```

All commands use local files and the standard library. The output file must not already exist. Inspect `residue_cycle`, `distinct_page_outputs`, and each candidate's page, offset, sign, complete output indices and matching-opening list.

For the interpretation of the common opening rule, compare the [prime-minus-one baseline](#/experiments/lp2-prime-minus-one-openings). The [ordinary-prime variant](#/experiments/lp2-prime-openings) illustrates a different source of duplicate coverage: schedules that differ only by a constant output shift.
