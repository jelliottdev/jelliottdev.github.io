# Why the reported 53-digit reverse-add result is a palindrome

## The precise claim

A [prior LP2-15 discussion](#/wiki/reported-attempts?section=lp2-15-prime-distance-palindromes) reports distances from word-level GP sums to nearby primes. After concatenating a selected sequence of those distances, the author added the 53-character decimal string to its reversal and obtained a 53-digit palindrome. The thread corrected an earlier 46-digit claim to 53 digits.

This experiment checks **that arithmetic and one conditional baseline**. The companion [word-by-word source audit](#/experiments/prime-distance-word-derivation) now reconstructs the same section from the archived LP2-15–16 rune text; its complete 57-word sequence differs from the 53 reported digits. This record retains the exact reported string as its input so the historical arithmetic claim remains independently inspectable. The source excerpt is identified in the [structured intake](data/reported-attempts.json) by SHA-256.

## Input and result

```text
  02311171210211215142515300303126131002122052400021111
+ 11112000425022120013162130300351524151211201217111320
= 13423171635233335155677430603477655153333253617132431
```

The addition is correct and the result reads identically in either direction. The first operand's leading zero is retained when constructing the reversal; as an integer it has no value, but dropping it before reversing would define a different operation.

The more informative fact is that **every paired digit sum is at most 7**. No column carries. If a decimal string has digits `d[0] ... d[n−1]`, adding it to its reversal pairs `d[i]` with `d[n−1−i]`. These pair sums are necessarily mirror-symmetric. Whenever all are below ten, and the outer pair is nonzero, the decimal result must be a palindrome. The reported example meets both conditions. Its palindromicity follows from this elementary rule; it does not require a cipher mechanism.

![Fifty-three paired sums from the reported digits mirror around the center and all remain below the decimal carry line of ten.](experiments/records/prime-distance-reverse-add/paired-sums.svg)

## A matched-digit control

The plan fixes 100,000 pseudorandom shuffles of the **same 53 characters**, with Python's `random.Random(3301)` and no restrictions on a leading zero in the shuffled string. Each shuffled string is reversed and added as an integer exactly as above. **50,442 of 100,000** shuffles yield palindromes. In this run, exactly the same 50,442 satisfy the no-carry condition with a nonzero outer pair.

This is a conditional, descriptive control: it preserves the selected digit multiset but not any GP word order. It is not a p-value for the full search that produced the string. That search could choose pages, word boundaries, nearest-prime ties, zero separators, and which examples to present. A null model for the whole idea must include those choices. Randomly shuffling uniform decimal digits would be a different and less relevant comparison, because the reported distances concentrate at small digits (11 zeroes, 18 ones, 11 twos).

## Reproduce

Extract the [experiment bundle](downloads/experiments/prime-distance-reverse-add.zip) with folders intact, then run from its root:

```text
python experiments/records/prime-distance-reverse-add/run.py --check
python experiments/records/prime-distance-reverse-add/check.py
python experiments/records/prime-distance-reverse-add/plot.py
```

The first command recomputes the arithmetic and all 100,000 fixed shuffles. The independent checker verifies the 53 column sums, their symmetry, the no-carry proof condition, and the saved control's internal consistency. The plotter regenerates the SVG from `results.json`. All use the Python standard library. `plan.json` specifies the original digits, seed, trial count and post-selection scope; `results.json` preserves the full paired-sum list and control counts.

## What remains open

The [companion audit](#/experiments/prime-distance-word-derivation) pins one source-to-digits derivation. Its archived first-section reading has 57 words, compared with 53 reported digits, and also yields a carry-free palindrome. The author's exact transcription or segmentation choices are not preserved in the supplied report. A full cipher test would still need a fixed operation on unsolved text and a comparison that repeats the complete choice of section, grouping and method.

This computational audit was run and checked by Codex on 2026-10-22. Human review of the source grouping and the mathematical interpretation is pending.
