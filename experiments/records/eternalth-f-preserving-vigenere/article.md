# Fixed-key Vigenère with a preserved F

**Result.** Under a page-local, 26-letter GP transliteration, the source's F-preserving encoder cannot produce **53 of 55** rune-bearing LP2 pages: each contains at least one letter that this operator can never output at its key position. LP2-03 and LP2-55 pass this necessary condition; that alone supplies no reading. The ordinary, invertible Vigenère branch produced **no English-like whole-page output** with the source's fixed key.

![At one key position F and X both become F, while N cannot appear; 53 of 55 pages violate the resulting output rule.](experiments/records/eternalth-f-preserving-vigenere/summary.svg)

The pinned [C++ draft](https://github.com/Eternalth/Liber-Primus/blob/a662136a916435767a74e6198f0549d5878b1d0a/VigenereFenglish.cpp) prints two versions with the eleven-letter key `AIRAUMFERAE`: ordinary A–Z Vigenère addition, and the same addition while leaving input `F` unchanged. Its key counter advances on every character, including `F`. We compiled the original and checked both outputs against an independent formula on [three synthetic inputs](experiments/records/eternalth-f-preserving-vigenere/source-parity.json). The source does not include a manuscript input or a recorded search result; the LP2 application here is a new bounded test.

## Why the F branch can be checked exactly

At the second key position the key letter is `I`, an offset of 8. The source maps input `F` to `F` because it preserves it. It also maps input `X` to `F` by addition. **No input maps to `N`** at that position: ordinary addition would require `F`, which the special rule does not shift. This makes the operator noninvertible. We enumerated all 26 inputs at every key position and checked that the same single forbidden output exists wherever the key offset is nonzero.

For the complete LP2 pages, concatenate the canonical Latin labels of the runes, including headings. Punctuation and spaces do not advance the key. Start the key at its first letter on each page. The resulting strings contain **291 forbidden-position letters** across 53 pages; LP2-00, for example, first violates the rule at zero-based Latin character 12. LP2-03 and LP2-55 contain none. A different transliteration, key phase, reset rule, or rune-level version is outside this result.

## Ordinary branch

The ordinary branch has a unique inverse: subtract the fixed key from the page's Latin letters. The best complete-page English quadgram score was **−7.894** on LP2-34, below the predeclared **−5.5** control threshold. None of the 55 pages crossed it. When the same complete-page search was repeated on 199 seeded pagewise rune shuffles, **152** shuffled searches scored at least as high as the actual best page. The shuffle comparison is a selection control, not a model of the cipher.

Nine archived 66-rune readings passed the English-score gate, and nine ordinary-key plants decoded exactly. Source-generated F-branch outputs passed the exhaustive forbidden-letter check; deliberately inserting a forbidden letter failed. The F branch has no general inverse, so we did not present subtraction with a preserved F as a source decryption algorithm.

The [plan](experiments/records/eternalth-f-preserving-vigenere/plan.json) fixes the page list, representation, key, controls and shuffle rules. [Results](experiments/records/eternalth-f-preserving-vigenere/results.json) give each page's forbidden-letter count and complete ordinary output. Run `python experiments/records/eternalth-f-preserving-vigenere/run.py --check`, then `python experiments/records/eternalth-f-preserving-vigenere/check.py` for an independent enumeration and full null check. The source repository has no license file, so its C++ file is linked and pinned rather than bundled.
