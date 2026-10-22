# A totient variant of the LP2-15 number panel

The printed [LP2-15](#/page/lp2-15) panel has sixteen integers. One is prime: the red **3299**. A supplied January 2026 discussion proposes taking Euler’s totient of the prime entries, subtracting the results from 3301, and reading Fibonacci gaps in the resulting prime positions. Its three 4×4 arrays make most of that proposal checkable. They do **not** specify a rule for turning the numbers into plaintext.

This audit keeps the reported arrays intact. The exact posted gap at row 4, column 1 is **317**, and the row 2, column 2 gap is marked uncertain; neither is silently corrected. The [source intake entry](#/wiki/reported-attempts?section=lp2-15-totient-before-prime-gap) identifies the supplied transcript and its SHA-256 hash.

![Every printed panel cell beside the source's prime candidate, ordinal and proposed Fibonacci gap](experiments/records/lp2-15-totient-gap-audit/panel-audit.svg)

## What the arithmetic actually does

Euler’s totient φ(n) counts positive integers at most n that are coprime to n. For a prime p, φ(p) = p − 1. Only **3299** is prime among the sixteen printed cells, so this first step changes only that cell, to **3298**. The source’s post-totient array matches the computed array in all 16 positions. It now has two adjacent 3298s.

For each post-totient value x, we calculated **both** 3301 − x and 3301 + x. The source’s second array matches one of these two values at every cell, and all sixteen selected values are prime. Fourteen selected values use subtraction; the entries **4516** and **1206** in the bottom row use addition, producing **7817** and **4507**. Thus the posted label “3301 − X” does not describe the whole array. A single literal subtraction rule would miss those two cells.

Primality alone leaves a further choice at both 3298 cells: **3** and **6599** are prime. Their zero-based prime ordinals are **1** and **852** respectively. Requiring a *Fibonacci-valued ordinal* selects 3, since 1 is a Fibonacci value and 852 is not. This filter leaves one sign per cell, but the source does not state it as a forward sign-selection rule. The two 3298 cells both become prime **3**, so ordinal **1** is duplicated and ordinal **0** (prime 2) is absent.

| Stage | Match with posted array | Qualification |
| --- | ---: | --- |
| Prime-only totient of printed panel | 16/16 | Changes only red 3299. |
| Candidate from 3301 ± transformed cell | 16/16 | Two cells require `+`; primality alone leaves two cells with either sign. |
| Selected candidate has Fibonacci zero-based prime index | 16/16 | This condition resolves the sign ambiguity after the candidate set is inspected. |
| Posted Fibonacci predecessor gap | 14/15 specified | Row 4, column 1 reports 317, while index 987 follows 610 and gives 377; one other cell is marked `?`. |

The gap calculation is easiest to see in the first row. Prime **43** has zero-based ordinal **13**; the preceding distinct Fibonacci value is **8**, so its gap is **5**. Prime **79** has ordinal **21**, following 13, so its gap is **8**. At bottom left, prime **7817** has ordinal **987**, following **610**, so the corresponding gap is **377**, not the posted 317. The source’s comment `0 /* ? */` leaves the other exceptional cell unresolved. Because the canonical Fibonacci sequence starts **0, 1, 1**, the predecessor of an occurrence of ordinal 1 also depends on which repeated 1 that occurrence is assigned to. The post does not give that assignment.

## What this settles—and what it does not

The arithmetic reproduces a coherent **derived pattern** from the printed square if the two plus signs and Fibonacci-index sign filter are allowed. It does not construct the original square from independent inputs: it begins with the printed numbers, changes the red one, and then selects signs that produce the reported primes. The established [Fibonacci-indexed prime construction](#/wiki/lp2-15-panel) starts independently with a declared index list, uses absolute distance from 3301, and matches all sixteen printed cells. These are different claims.

No rule is supplied for which of the source’s arrays should become a cipher key, how it advances through runes, what to do with the duplicate 3 or uncertain gap, or how to score a result. The discussion itself suggests only that a related manipulation *might* apply to the text. This record therefore audits the numbers; it is **inconclusive as a decoding method**.

## Reproduce the audit

From the repository root or this experiment’s extracted ZIP, use Python 3 with no external packages:

```text
python experiments/records/lp2-15-totient-gap-audit/run.py --check
python experiments/records/lp2-15-totient-gap-audit/check.py
python experiments/records/lp2-15-totient-gap-audit/plot.py --check
```

The [plan](experiments/records/lp2-15-totient-gap-audit/plan.json) fixes the source’s three arrays and source hash. The [results](experiments/records/lp2-15-totient-gap-audit/results.json) retain both signs, primality and prime ordinal for every cell. The independent checker uses a sieve and a coprimality count rather than the producer’s factoring and totient implementation. Neither script chooses a plaintext interpretation.
