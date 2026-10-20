# What do the missing word repetitions constrain?

**Every selected ciphertext token is distinct:** 1,589 tokens when apostrophes are boundaries, or 1,591 when apostrophes are transparent. Allowing anagrams adds four pairs of four-rune tokens, but no pairs of five or more runes. These are constraints on particular word-local models, not a proof that every word-based cipher is impossible.

## Exactly which tokens are counted?

Read archived LP2-00–55 one page at a time, retaining headings. Slashes and CR/LF line wraps do not break a token. Other nonrune characters are boundaries. Run the analysis twice: once with apostrophes as boundaries, once with apostrophes ignored. No Latin expansion is used: TH and NG each count as one rune.

Drop the first and last nonempty token of each page before comparing. Those units may be fragments at page edges. This deliberately omits some complete words too; it avoids assuming that the printed page edges are word boundaries. Do not join pages. Keep only the remaining tokens containing at least four ciphertext runes.

| Apostrophe policy | Selected tokens | Distinct exact tokens | Equal pairs | Anagram pairs, length ≥4 | Anagram pairs, length ≥5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Boundary | 1589 | 1589 | 0 | 4 | 0 |
| Transparent | 1591 | 1591 | 0 | 4 | 0 |

A pair means two distinct token occurrences, even if they are on the same page. A group of k equal signatures contributes k(k−1)/2 pairs. The ledger identifies every selected token, its original page-local token index and each rune's source offset, plus all collision groups.

## Model 1: a deterministic cipher reset for each word

Suppose each printed ciphertext token comes from one plaintext unit through the same deterministic function F, with identical key and reset context:

```text
ciphertext unit = F(plaintext unit)
```

Equal inputs to the same function produce equal outputs. Therefore, if two ciphertext units differ, their plaintext units cannot have been equal under that model. Since all selected ciphertext tokens differ, their corresponding plaintext units must differ wherever the same F applies.

The function may contain a complicated composition, deterministic padding, fractionation or hashing. None of that changes the equal-input implication. F need not be invertible, and plaintext length need not equal ciphertext length. The four-rune cutoff is a selection rule on the observed ciphertext only.

This does **not** prove the unknown plaintext repeats. It supplies a necessary condition for this model, rather than a general exclusion of deterministic word ciphers.

## Model 2: a shared symbol map plus word-local shuffling

A different proposal applies the same symbol map to every word, then independently rearranges each word's output. Identical plaintext words may now give different ordered ciphertext, but they must give the same multiset of ciphertext symbols: they must be anagrams.

For example, A B A mapped to 2 5 2 can be rearranged into 2 2 5 or 5 2 2. The order changes, but the two 2s and one 5 remain. This implication does not require an injective symbol map; each input rune only needs one fixed output rune.

There are no selected anagram pairs of length five or more. Thus no two such tokens can encode the same plaintext rune word under this shared-map-and-shuffle model. Among length-four-or-longer selected tokens, at most four occurrence pairs can represent repeated plaintext words. An anagram match is only necessary, not proof that a pair encodes the same word.

Unlike Model 1, this model preserves rune length. Padding, fractionation, or a different substitution for each word changes its assumptions.

## The four anagram pairs

Both apostrophe policies produce these same pairs. Spaces below separate rune labels; NG, EA, TH, OE and AE each denote one rune. Token indices are zero-based in the original per-page token list, before removing edge tokens.

| First occurrence | Second occurrence |
| --- | --- |
| [LP2-42](#/page/lp2-42), token 4: **F A NG E** | [LP2-53](#/page/lp2-53), token 16: **E F A NG** |
| [LP2-12](#/page/lp2-12), token 40: **EA TH W Y** | [LP2-46](#/page/lp2-46), token 59: **Y EA TH W** |
| [LP2-10](#/page/lp2-10), token 60: **S N OE X** | [LP2-12](#/page/lp2-12), token 33: **OE S N X** |
| [LP2-09](#/page/lp2-09), token 17: **J Y T AE** | [LP2-49](#/page/lp2-49), token 9: **T Y AE J** |

These are ciphertext comparisons, not proposed readings. The resemblance of a label sequence to a familiar word is not evidence of plaintext.

## What changing context does

An algorithm can be deterministic while its output depends on position, carried state, a different key, or a nonce. Those inputs belong to the effective context. If they differ, equal plaintext words need not give equal ciphertext. A Vigenère key continuing between words is not automatically a reset-per-word cipher.

Likewise, allowing a different symbol map for each word can destroy the anagram relationship. Two copies of A B A could map to 0 1 0 and 2 3 2; their multiplicity patterns agree, but their named-symbol multisets differ. This experiment does not test that more flexible model.

## Reproduce and independently check

Download and extract the experiment ZIP with folders intact. Python 3's standard library is enough; no packages, network requests or AI calls are required.

```text
python experiments/records/word-reset-repetition/run.py --check
python experiments/records/word-reset-repetition/check.py
```

The main script scans characters and groups sorted rune sequences. The independent checker reads page JSON, tokenizes with a regular expression, and compares 29-component count vectors. It verifies source positions and every collision group, and checks the anagram implication over 4,374 small mapping/permutation cases, including noninjective maps.

Both input formats share their archival source; this is not a second visual transcription audit. The supplied closure archive reports the same observations in C31 and C33. This record freshly reproduces them and explains the elementary implications. It does not rerun or claim verification of the archive's Lean project.

## Scope of the conclusion

The counting is exact for these token rules. No English frequency model, likelihood, p-value, or assumption that a particular word must appear is used. Changed boundaries, page-edge inclusion, a corrected transcription, different contexts, or a different output construction require an explicitly recorded retest. The word-length article uses a different boundary convention for a different purpose; its total should not be substituted for the counts here.
