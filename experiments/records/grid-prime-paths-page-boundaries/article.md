# Prime paths with manuscript page boundaries

This variant asks whether the baseline’s exact three-value missing set survives when every four-cell path must stay on a single manuscript page. It does not: **1103 and 3011 become absent as well**. The original absent values, 1033, 2213 and 3301, remain absent.

“Not supported” applies to preserving the same three-value missing set under this change. It does not reject the baseline recount or rule out a cipher.

## The one changed rule

The [baseline](#/experiments/grid-prime-paths) stacks all 32 rows from LP2-49–51 and permits paths to cross the two page joins. This variant keeps the same row order, columns and coordinate system but rejects a path unless all four cells belong to one page.

Everything else stays fixed: four consecutive cells, eight straight directions, no wrapping or turns, reject any path containing a first character of 4, permit leading zeroes, test primality in decimal, and retain the suffix extraction and separate base-4 value. No cells are deleted or moved.

## Results compared with the baseline

| Measurement | Joined-page baseline | Within-page variant |
| --- | --- | --- |
| Geometrically valid directed paths | 1,364 | 1,148 |
| Eligible after rejecting digit 4 | 1,058 | 876 |
| Decimal-prime occurrences | 191 | 151 |
| Distinct decimal primes | 46 | 44 |
| Candidate prime values | 49 | 49 |
| Missing values | 1033, 2213, 3301 | 1033, 1103, 2213, 3011, 3301 |

The removed set contains 216 directed paths, of which 182 have no digit 4 and 40 pass the decimal-prime filter. The remaining 151 hits equal exactly the baseline’s within-page subset, including their complete source coordinates and extracted strings. The variant produces no new hits.

## Why 1103 and 3011 disappear together

The baseline has one occurrence of 1103:

```text
LP2-49 row 10, column 8: 1M
              page boundary
LP2-50 row  1, column 8: 15
LP2-50 row  2, column 8: 0Z
LP2-50 row  3, column 8: 3Q

Forward first characters: 1103
Reverse first characters: 3011
```

Reading those same four cells backward produces the sole occurrence of 3011. Forbidding the boundary crossing removes both. These are two directed hits on one undirected path, not independent locations. This illustrates why counting multiple related observations does not automatically multiply the evidence for an interpretation.

## Reproduce

Extract the experiment ZIP with its directory structure intact. No external packages or network access are required.

```text
python experiments/records/grid-prime-paths-page-boundaries/run.py --check
python experiments/records/grid-prime-paths-page-boundaries/check.py
```

The producer enumerates starts and direction vectors from the archived grid export. The checker instead rebuilds tokens directly from page records, enumerates endpoint pairs and uses a sieve for primality. Both enforce the same page barrier. The output retains every hit and all 49 candidate frequencies, including zeroes.

## What this comparison establishes

The exact missing set depends on whether page joins are searchable. Neither convention is proved to be the intended one. Since this variant only removes paths, it cannot restore a value already absent from the baseline; continued absence of the original three is therefore not an independent confirmation.

This is a deterministic scope comparison, not a statistical test. A chance model would need to preserve or deliberately change the relevant page structure and account for the exploratory choice of statistic. Further changes to layout, path length, numeral base or allowed directions belong in separately declared variants of this family.
