# Can the reported prime-distance digits be derived from LP2-15–16?

The earlier [reverse-add record](#/experiments/prime-distance-reverse-add) checks the arithmetic of a reported 53-digit string. It does not show how each digit came from the manuscript. This source audit makes that missing step explicit: read every word in the same first section, sum its Gematria Primus rune values, and record its distance to the nearest prime.

The archived transcription yields **57 word distances**, while the supplied report lists **53**. The two strings have a minimum digit-edit distance of seven under ordinary insertion, deletion and substitution. That discrepancy matters for reproducing the reported derivation. It does **not** make the reverse-add observation disappear: the complete 57-digit sequence also produces a palindrome on the first addition.

## Frozen reading rule

The input is the archived [LP2-15](#/reader/lp2-15) and [LP2-16](#/reader/lp2-16) rune transcription. We use the two-word heading on LP2-15, then every rune word after its `$` section marker through the word before the next section's `ᛈᚹᚷᚷ` on LP2-16. The first five values agree with the report's “red header” sequence; the first three body words are red on the page image. Printed square numbers are not words in this calculation.

A hyphen or period separates words. A `/` followed by a line break is typographic wrapping, so runes on either side remain one word unless a hyphen intervenes. The page boundary also does not split its continuing word. For each word, sum the first 29 primes in Gematria Primus order and use the *absolute* distance to the closest integer prime. A tie between equidistant primes does not change the distance. The [plan](experiments/records/prime-distance-word-derivation/plan.json) pins both text hashes, the rune-to-prime table, the section end marker and the report's 53 digits.

For example, the heading words give `ᚠᚢᛚᛗ → 149 → 0` and `ᚪᛠᚣᛟᚪ → 489 → 2`. The [full token trace](experiments/records/prime-distance-word-derivation/results.json) lists all 57 words, their prime sums and nearest-prime distances, so any disputed separator or rune has an exact place to challenge.

## Where the sequences differ

```text
Reported: 02311171210211215142515300303126131002122052400021111   (53 digits)
Archive:  023111712102410211215142515300303126141002122142400021111 (57 digits)
```

![The reported 53 digits aligned with 57 distances independently derived from archived LP2-15–16 words. Ochre columns mark gaps or differing digits.](experiments/records/prime-distance-word-derivation/word-distance-alignment.svg)

[Open the alignment at full size](experiments/records/prime-distance-word-derivation/word-distance-alignment.svg).

The figure shows **one** minimum alignment: four archive word positions have no partner in the report and three paired digits differ. The minimum edit count is independently checked by dynamic programming. Repeated digits make the precise alignment non-unique, so these positions should not be read as proof of which words the original author skipped or transcribed differently. The reported list and archived source cannot be made identical under the stated rule without additional choices or corrections.

## What happens to the palindrome?

Adding the archive-derived string to its reversal gives:

```text
  023111712102410211215142515300303126141002122142400021111
+ 111120004241221200141621303003515241512112014201217111320
= 134231716343631411356763818303818367653114136343617132431
```

The [independent checker](experiments/records/prime-distance-word-derivation/check.py) verifies the integer sum and each mirrored digit pair. The largest paired sum is eight, so no decimal carry occurs. That is why the 57-digit sum remains a palindrome.

As a conditional baseline, we shuffled the same **57 distance digits** 100,000 times with a fixed seed, reversed and added each shuffle, and obtained **53,845 palindromes**. This preserves the short-digit distribution that makes carry-free addition frequent. It does not reproduce the full historical search over pages, section boundaries and prime-related transformations. The sibling record's 53-digit control gives 50,442 palindromes in 100,000 shuffles of *its* fixed digit multiset. Neither rate is a probability of intentional construction.

## Reproduce and limits

From a full checkout or the [experiment ZIP](downloads/experiments/prime-distance-word-derivation.zip), run:

```text
python experiments/records/prime-distance-word-derivation/run.py --check
python experiments/records/prime-distance-word-derivation/check.py
python experiments/records/prime-distance-word-derivation/plot.py --check
```

The first command recomputes every word and all 100,000 shuffles. The checker uses a separate word scanner, a different nearest-prime search, direct column arithmetic, a minimum-edit calculation and a second control replay. The supplied discussion is identified by SHA-256 in the [reported-attempt intake](#/wiki/reported-attempts?section=lp2-15-prime-distance-palindromes); its full pasted transcript is not redistributed. The report may have used a different transcription or unpublished segmentation choices. Image-level verification of every word break and human review are still pending.

This is an **input-derivation audit**, not a decryption of LP2-15–22. A future cipher test would need a fixed way to use these distances on an unsolved passage and evaluate the complete output on text that did not determine the rule.
