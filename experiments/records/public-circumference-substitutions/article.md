# The circumference substitutions

A [public failed-attempt record](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/2%CF%80R/README.md) applies a circumference-inspired rule to each GP rune: use either its alphabet position or its associated prime as the radius, multiply by `2π`, then reduce modulo 29. The README says **round**, but the repository's [index-radius output](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/2%CF%80R/pages_2piR.txt) and [prime-radius output](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/2%CF%80R/pages_2piR_primes.txt) use **integer truncation** instead. We replay both interpretations so the source discrepancy is visible.

## Finding

![Distinct output runes under index and prime radii with nearest rounding or truncation.](experiments/records/public-circumference-substitutions/mapping-coverage.svg)

On LP2-00–55, the truncated index and prime maps reproduce the first nine runes on all **55 rune-bearing pages** in the pinned public outputs. LP2-50 has no runic line to compare. The README's nearest-rounding rule does not reproduce those outputs. It produces a different symbol map: the index version reaches 25 of 29 possible output runes instead of 26 under truncation. With GP prime values as radii, both rounding choices reach only **18 of 29** output runes, although the actual mappings differ.

Each rule is a fixed one-rune substitution. In the prime-radius version, 11 output symbols are unreachable. This compression makes the rule non-invertible without additional information; it does not by itself establish that the manuscript was encoded by the inverse rule. The source reports no interesting reading, but supplies no scoring threshold or test that would justify a blanket negative conclusion. Our reproducible result is the exact map and the output agreement.

## Method and limits

The [plan](experiments/records/public-circumference-substitutions/plan.json) pins the public revision, source-output hashes, two radius choices and two rounding choices. The [results](experiments/records/public-circumference-substitutions/results.json) contain all four 29-entry maps and hashes of the transformed text for LP2-00–55. The [independent check](experiments/records/public-circumference-substitutions/check.py) uses a separate floor-based calculation, checks every saved output hash, and can compare both source text files when supplied locally. Punctuation, line marks and decimal numbers remain unchanged; only runes are substituted.

This test neither scores candidate English nor searches secondary keys, alternative page groupings, or a reversible decoding scheme. In particular, a numerical motif is not evidence for a cipher merely because it can be applied to every symbol.

## Reproduce

Run `python experiments/records/public-circumference-substitutions/run.py --check` and `python experiments/records/public-circumference-substitutions/check.py`. For the source-output comparison, put the two text files named in the [plan](experiments/records/public-circumference-substitutions/plan.json) in one directory and run `check.py --source-directory PATH`. Their SHA-256 values are verified before comparison.
