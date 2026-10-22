# Crib differences as a source-stream search

A proposed approach is to guess a plaintext word, subtract its Gematria Primus indices from the aligned ciphertext indices, and look for that difference sequence elsewhere in *Liber Primus*. This record runs one fixed version of that idea. **Nine exact three-rune matches occur, fewer than the 10.615 mean in 2,000 page-preserving shuffles.** It does not identify a key source or test a decryption.

![Histogram of matching windows across 2,000 within-page shuffles, with the nine observed matches highlighted.](experiments/records/crib-difference-stream-search/matching-windows.svg)

The suggestion was supplied in a 25 September 2026 discussion. It gave no fixed cribs, positions, direction of subtraction or source scope. Those choices here are ours, made for a bounded test. This is **not** a replay of an unpublished result by the poster.

## Rule fixed before the scan

The target is the three red runes opening the lower block of [LP2-39](#/page/lp2-39), with zero-based alphabet indices **27, 5, 15**. We reuse the existing [20-word header-crib list](#/experiments/lp2-39-header-cribs) rather than selecting words after seeing source hits. Exact GP spelling and segmentation leave **17 three-rune candidates**, each producing a distinct difference triplet. For a candidate with plaintext indices P and target indices C, the proposed key triplet is `(C − P) mod 29`. For example, WAY becomes indices 7, 24, 26 under the stored alphabet and gives 20, 10, 18. The [plan](experiments/records/crib-difference-stream-search/plan.json) fixes the entire rule.

Search the other **71 archived text pages**, LP1 and LP2, for an exact forward occurrence of each triplet. Remove punctuation but keep rune order. A three-rune window may cross a printed word or row break within one page; it may not cross a page boundary. No reverse direction, gaps, alphabet rotation, wildcard or prime-value subtraction is allowed. The LP2-39 target page is excluded from its own source search.

| Measure | Result |
| --- | ---: |
| Source runes | 15,693 |
| Three-rune crib candidates | 17 |
| Matching source windows | 9 |
| Different candidate triplets with a hit | 9 |
| Control mean, 2,000 within-page shuffles | 10.615 |
| Shuffles with at least nine hits | 1,499 / 2,000 |

The inclusive upper-tail Monte Carlo estimate is `(1499 + 1) / 2001 = 0.7496`. The lower-tail estimate is 0.3833. Neither suggests an unusual excess or deficit of matches under this control. The [complete JSON](experiments/records/crib-difference-stream-search/results.json) lists every candidate spelling, derived triplet, page and zero-based rune offset, plus the complete control histogram. A hit is a sequence coincidence, not a plaintext reading.

## Why the comparison matters

Each shuffled source preserves every page's rune count and length while destroying its original order. The same 17 triplets are searched in every shuffled collection. This accounts for trying the entire fixed crib list, rather than judging whichever single candidate happens to match. It does not model an author's construction process, and it destroys real repeated words and other local structure. The candidate list and three-rune target were already available before this plan, so the result cannot be treated as a prospective test of the broad idea.

A planted positive control inserts the first derived triplet at rune offset zero of the first source page; the scanner recovers it. A separate checker reconstructs source streams from individual stored lines, independently recomputes the GP differences and all observed hits. The producer reruns the seeded shuffles byte for byte.

## Reproduce and extend

Download this record's experiment bundle and run Python 3.12 or later, with no packages or network connection:

```text
python experiments/records/crib-difference-stream-search/run.py --check
python experiments/records/crib-difference-stream-search/check.py
python experiments/records/crib-difference-stream-search/plot.py --check
```

An actual cipher test would need a longer independently chosen crib, a justified key-source location and a rule that predicts **withheld** ciphertext. Searching a longer phrase after seeing these hits, trying both subtraction directions, or allowing interrupted matches creates new search space and needs a new plan and controls. This record leaves those possibilities open; it only tests the rule and source scope above.
