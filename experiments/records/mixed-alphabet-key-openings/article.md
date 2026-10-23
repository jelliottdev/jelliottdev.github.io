# Keyword-mixed GP alphabets

What changes if a candidate word rearranges the 29-rune alphabet before the usual Vigenère arithmetic?

## Finding

**No exact opening match.** The 43 archived words form 43 mixed alphabets. Across every key phase and 55 rune-bearing unsolved pages, **309 settings** gave **152,955 comparisons** with nine fixed, 12-rune openings. None matched; the closest agreed for four runes. This rules out those exact openings under this one mixed-alphabet convention, not keyword alphabets generally.

![The first archived key moves its unique runes to the beginning of the GP order.](experiments/records/mixed-alphabet-key-openings/clock.svg)

The diagram uses the first archived key. Its repeated letters are included once, in their first-seen order; the remaining GP runes follow in ordinary order. The lower row gives the *original GP indices* that occupy the first twelve positions of this new alphabet. Both ciphertext and key symbols are located in that mixed order, their positions are subtracted modulo 29, and the resulting position is mapped back to a rune. Changing only the key string in ordinary Vigenère would be a different operation.

## Scope and reproduction

This is a **new bounded test**, using the previously pinned [43-key source list](#/experiments/public-wordlist-vigenere). The rule resets at each page and tests all phases of each source key. It retains headings and ignores non-rune marks. Alternative keyword-normalization rules, mixed plaintext/key alphabets, other source words and later plaintext positions are outside this test. A planted plaintext was encrypted and recovered under the same mixed alphabet; the independent checker repeated the full page-start census from page JSON.

The exact rule is in the [manifest](experiments/suites/classical-key-schedules/manifest.json), with [results](experiments/records/mixed-alphabet-key-openings/results.json). From the repository root, run `python experiments/records/mixed-alphabet-key-openings/run.py --check` and `python experiments/suites/classical-key-schedules/check.py mixed-alphabet-key-openings`.
