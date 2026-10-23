# The circumference substitutions

A [public failed-attempt record](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/2%CF%80R/README.md) applies a circumference-inspired rule to each GP rune: use either its alphabet position or its associated prime as the radius, multiply by `2π`, then reduce modulo 29. The README says **round**, but the repository's [index-radius output](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/2%CF%80R/pages_2piR.txt) and [prime-radius output](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/2%CF%80R/pages_2piR_primes.txt) use **integer truncation** instead. We replay both interpretations so the source discrepancy is visible.

## Finding

![Distinct output runes under index and prime radii with nearest rounding or truncation.](experiments/records/public-circumference-substitutions/mapping-coverage.svg)

The truncated index and prime maps reproduce the **complete Latin rune-label streams on all 57 pages** in each pinned public output, including the source's page 56. The published LP2-00–55 test spans 56 of those pages; LP2-50 has no runic line. The README's nearest-rounding rule does not reproduce those outputs. It produces a different symbol map: the index version reaches 25 of 29 possible output runes instead of 26 under truncation. With GP prime values as radii, both rounding choices reach only **18 of 29** output runes, although the actual mappings differ.

Each rule is a fixed one-rune substitution. In the prime-radius version, 11 output symbols are unreachable. This compression makes the rule non-invertible without additional information; it does not by itself establish that the manuscript was encoded by the inverse rule. The source reports no interesting reading, but supplies no scoring threshold or test that would justify a blanket negative conclusion. Our reproducible result is the exact map and the output agreement.

## Method and limits

The [plan](experiments/records/public-circumference-substitutions/plan.json) pins the public revision, source-output hashes, two radius choices and two rounding choices. The [results](experiments/records/public-circumference-substitutions/results.json) contain all four 29-entry maps and hashes of the transformed text for LP2-00–55. The [independent check](experiments/records/public-circumference-substitutions/check.py) uses a separate floor-based calculation, checks every saved output hash, and compares complete rune-label streams when both source text files are supplied. The [source-output certificate](experiments/records/public-circumference-substitutions/source-output-certificate.json) records all 57 comparisons per source file. Punctuation, line marks and decimal numbers remain unchanged; only runes are substituted.

The original plan's source-file hashes describe a Windows **CRLF checkout**. The pinned Git files have **LF** line endings. The checker verifies the LF Git bytes, then verifies that changing only those line endings to CRLF yields the original plan's hashes. No source content or original plan was changed. For label comparison, it normalizes the archived `IO`/`IA` spelling, excludes structured eight-cell alphanumeric grid rows, and compares complete joined labels without guessing word breaks.

This test neither scores candidate English nor searches secondary keys, alternative page groupings, or a reversible decoding scheme. In particular, a numerical motif is not evidence for a cipher merely because it can be applied to every symbol.

## Reproduce

Run `python experiments/records/public-circumference-substitutions/run.py --check` and `python experiments/records/public-circumference-substitutions/check.py`. For the complete source-output comparison, put the two text files named in the [plan](experiments/records/public-circumference-substitutions/plan.json) in one directory and run `check.py --source-directory PATH`. Both LF and CRLF copies are accepted after the two byte receipts are verified.
