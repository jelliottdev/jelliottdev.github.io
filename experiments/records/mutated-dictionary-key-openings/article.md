# One-rune changes to a public key list

## Finding

None of the altered keys produced any of **nine specified 12-rune readings at the start of any of 55 rune-bearing LP2 pages**. The test covered both GP29 arithmetic directions and every phase of each altered key. It says nothing about other plaintext beginnings, positions inside a page, or whether a full decoded page reads as language.

![The two declared changes to 43 source keys collapse to 9,856 distinct altered keys. Every phase and two arithmetic directions give zero exact matches to nine fixed openings on 55 pages.](experiments/records/mutated-dictionary-key-openings/mutation-scope.svg)

The [public 43-key replay](#/experiments/public-wordlist-vigenere) used the keys as written. This follow-up tests a different, finite suggestion: a plausible key might have one wrong GP rune. We tested two ways to interpret that suggestion:

- **One position:** replace one rune at one position of a key.
- **One rune type:** replace every occurrence of one selected rune in that key, as in the proposed `CIRCUMFERENCE` → `FIRFUMFERENFE` analogy.

For either rule, each replacement is one of the other 28 GP runes. Different descriptions can produce the same changed key, so the **15,708 named changes** reduce to **9,856 distinct keys**. Across their phases, these yield 83,328 key settings. This is one bounded key-variation test, not thousands of separate ideas.

## How the check works

At each page start, the first twelve ciphertext runes and one specified reading determine exactly twelve required key values. We computed those requirements once for each page–reading pair and each arithmetic direction. A changed key matches only if its twelve values at a particular phase equal one of those required vectors. This indexed comparison is exactly equivalent to decoding every named case, but avoids repeating over 82 million trivial comparisons.

The [frozen plan](experiments/records/mutated-dictionary-key-openings/plan.json) pins the 43 source keys, 56 page transcriptions, nine readings, rules, and hashes. [Results](experiments/records/mutated-dictionary-key-openings/results.json) contain the candidate-clock digest, counts and any exact hits. Both an encoder/decoder planted control and a separate enumerating checker pass. The result is **zero exact matches** under this fixed opening test; it is not a whole-page English-language score.

## Reproduce

Run `python experiments/records/mutated-dictionary-key-openings/run.py --check` and `python experiments/records/mutated-dictionary-key-openings/check.py` from the repository root. Both require only Python's standard library and the declared repository inputs.
