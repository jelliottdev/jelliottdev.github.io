## What was tested?

The lower text block on [LP2-39](#/page/lp2-39) starts with three red runes, followed by punctuation. The first rune is enlarged across several rows. Read in manuscript order, the archived prefix is IA + C + S, with zero-based indices 27, 5 and 15. The Latin labels describe the ciphertext symbols; they are not an English reading.

A **crib** is a proposed plaintext fragment. This experiment takes twenty suggested words and asks whether any single affine substitution maps the word to those three runes. It checks the entire declared key space, rather than adjusting a separate shift for each position.

The candidate list is fixed in plan.json. It is a selected list, not a dictionary or an unbiased sample of possible headings. WHY was already in the list before this calculation; no new words were added after inspecting the result.

## Representation comes before the key search

Words are uppercased and split in every possible way using the 29 Latin labels stored in the [GP alphabet and rune values](#/wiki/rune-values). There are no pronunciation rules or spelling substitutions. TH may be one label or T + H; NG may be one label or N + G.

BEING does **not** have a three-rune representation under these rules. Its two segmentations are B + E + I + NG (four) and B + E + I + N + G (five). The suggested B + EI + NG would need an EI label that is absent from this alphabet. A proposed alias can be tested separately, but it must be declared rather than silently substituted.

THUS has three runes as TH + U + S, or four as T + H + U + S. Their prime sums are 61 and 138 respectively. These sums are recorded for transparency; primality is not used to select a candidate or key. See [word lengths](#/wiki/word-lengths) and [spelling and prime sums](#/wiki/prime-sums).

## Search bounds and complete result

The encryption rule is C = (aP + b) mod 29, using rune indices rather than prime values. Test every a from 1 through 28 and every b from 0 through 28: **812 keys**. Multiplication by any allowed a is invertible modulo 29. This space includes ordinary shifts and shifted alphabet reversals.

The twenty words give 22 segmentations. Seventeen have the required three runes, so the complete search contains **17 × 812 = 13,804 candidate/key trials**. Wrong-length candidates are retained below instead of disappearing from the report.

| Candidate | Rune lengths | Result |
| --- | --- | --- |
| AND | 3 | No affine fit |
| BUT | 3 | No affine fit |
| WHY | 3 | a = 7, b = 7 |
| HOW | 3 | No affine fit |
| WHO | 3 | No affine fit |
| YOU | 3 | No affine fit |
| HER | 3 | No affine fit |
| HIM | 3 | No affine fit |
| HIS | 3 | No affine fit |
| ONE | 3 | No affine fit |
| TWO | 3 | No affine fit |
| WAY | 3 | No affine fit |
| MAP | 3 | No affine fit |
| LAW | 3 | No affine fit |
| GOD | 3 | No affine fit |
| BEING | 5, 4 | Wrong length |
| OLD | 3 | No affine fit |
| THUS | 3, 4 | No affine fit |
| FOLLY | 5 | Wrong length |
| WISDOM | 6 | Wrong length |

Only WHY matches. Its rune indices are W = 7, H = 8 and Y = 26. The single key a = 7, b = 7 produces:

| Position | Proposed index P | 7P + 7 | Reduced modulo 29 | Cipher label |
| --- | --- | --- | --- | --- |
| 1 | 7 | 56 | 27 | IA |
| 2 | 8 | 63 | 5 | C |
| 3 | 26 | 189 | 15 | S |

## Why this is not a solution

Three symbols provide very little independent constraint. Because the first two proposed indices differ, they determine an affine key; the third position tests that key. Here the check was repeated across seventeen eligible candidates. Finding one fit does not establish that the authors intended WHY, or that this key applies to the following text.

For this three-symbol ciphertext, the 812 invertible affine keys produce 812 distinct three-symbol candidate plaintexts. A short word among those outputs needs further evidence. This is a search-space count, not a probability estimate for English words or for the authors' choices.

This experiment does not score the remaining text, use a language model, or select a key by how promising the continuation sounds. The recorded outcome is **inconclusive** about the reading. The exact header fit is reproducible; a decipherment is not established.

A follow-up should freeze the surviving key and test text outside the three-rune crib against an explicit criterion. If it fails, inventing fresh per-position shifts would define a different method, not rescue this affine result. Keep such changes in separate variants within this family. See [search space and bounds](#/wiki/search-space) and [cipher invariants](#/wiki/cipher-invariants).

## Reproduce and inspect

Download this experiment's ZIP and extract it with its folders intact. Both commands use Python's standard library and run offline:

```text
python experiments/records/lp2-39-header-cribs/run.py --check
python experiments/records/lp2-39-header-cribs/check.py
```

The first script enumerates label prefixes and all affine keys. The independent checker enumerates every possible cut in each spelling, locates the header from the archived paragraph boundary, and derives a key algebraically from the first two positions before checking the third. It does not import the search implementation.

results.json retains every segmentation, its indices, rune count, prime sum and matching keys. plan.json fixes the candidate list, normalization, source position and key bounds. Changing any of these should produce a named variant, with the old result retained for comparison.
