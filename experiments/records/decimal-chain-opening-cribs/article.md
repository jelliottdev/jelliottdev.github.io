# Five-digit chain-addition keys

Could a five-digit decimal primer generate the shifts for the beginning of an unsolved page?

## Finding

**None of the 100,000 primers recovered a fixed known opening.** We tested both addition and subtraction against the first 12 runes of all 55 rune-bearing unsolved pages. That is **99 million exact comparisons** with nine preselected known readings, with zero 12-rune matches. The longest shared prefix was **five runes**. Four page/reading/sign combinations admit a primer for those first five runes, but the sixth rune breaks each one. Five chosen digits can fit five chosen shift values; those short fits do not support a decryption.

![A five-digit decimal primer generates later key digits by adjacent-pair addition modulo ten.](experiments/records/decimal-chain-opening-cribs/primer-clock.svg)

The example starts with `31415`. Its sixth digit is `(3 + 1) mod 10 = 4`; its seventh is `(1 + 4) mod 10 = 5`. The same rule continues. The [American Cryptogram Association's GROMARK sheet](https://www.cryptogram.org/downloads/aca.info/ciphers/Gromark.pdf) specifies a five-digit primer and this chain addition, but the complete cipher also uses a mixed alphabet. **This experiment isolates the digit stream** and uses its digits as direct GP29 shifts. It is a newly constructed LP2 baseline, not a replay of a documented historical attempt or a test of full GROMARK.

## What was checked

Every decimal primer from `00000` through `99999`, including leading zeroes, produced 12 key digits. For each page, we reset the stream at the first visible rune, kept the header, and ignored non-rune marks. We computed `plaintext = ciphertext ± digit (mod 29)` and compared with the same nine 12-rune openings used in earlier bounded tests. The [result file](experiments/records/decimal-chain-opening-cribs/results.json) gives the complete prefix-length histogram for both signs. A synthetic known reading encrypted with primer `31415` is recovered under each sign.

The [plan](experiments/records/decimal-chain-opening-cribs/plan.json) fixes the primer range, recurrence and criterion. Run `python experiments/records/decimal-chain-opening-cribs/run.py --check` and `python experiments/records/decimal-chain-opening-cribs/check.py` from the repository root. The checker independently reads page JSON and counts matching prefixes by enumerating all 100,000 streams. Other page positions, unknown openings, nondecimal primers, alternate GP alphabets, interruptions and full GROMARK are outside this result.
