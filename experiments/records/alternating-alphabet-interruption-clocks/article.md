## Finding

**Neither clock rule revealed a declared opening.** The test tried two known Liber Primus keys with alternating cipher alphabets on 55 LP2 pages. Across **1,664 settings and 823,680 comparisons**, no output matched any of the nine fixed twelve-rune openings. The longest matching beginning was three runes.

This checks one specific way an F rune might interrupt a cipher. It does not show that alternating alphabets or interruptions are absent from LP2. A real plaintext could simply begin differently from every opening in this test.

![Two rows show which alphabet reads each rune when F pauses just the key or both clocks.](experiments/records/alternating-alphabet-interruption-clocks/clocks.svg)

## What changes at an F?

Each alphabet has its own repeating key. Alphabet A uses ordinary GP rune order; B reverses that order. Normally the decoder switches between A and B after every rune, advancing the key it just used.

The two policies differ when the **ciphertext** rune is F:

| Rule | Selected key | Alphabet for the next rune |
|---|---|---|
| Pause the key | Keep its current position | Switch A ↔ B |
| Pause both clocks | Keep its current position | Keep the same alphabet |

**F is still decoded using the current key.** It is not removed, copied into the plaintext, or treated as a verified word separator. That distinction matters: those would be different ciphers.

## What was tested?

The two key vectors are the previously documented Welcome and second-koan keys. Both assignments to A/B are tested. Each key may start at any phase; either alphabet can go first; and both addition and subtraction are included. All state resets at the beginning of each page. Spaces, punctuation and other non-runes do not advance either clock.

| Test | Pause key | Pause both |
|---|---:|---:|
| Settings | 832 | 832 |
| Page openings decoded | 45,760 | 45,760 |
| Exact comparisons | 411,840 | 411,840 |
| Twelve-rune matches | **0** | **0** |
| Longest matching prefix | 3 | 3 |

The target pages are LP2-00–55, including headings. LP2-50 contains no recognized runes in the archived text layer and is excluded, leaving 55 pages. Each decoded head is compared with the same nine openings used in the [known-key baseline](#/experiments/lp2-known-vigenere-keys). No English score decides success, and no crib was chosen after inspecting the outputs. Counts include every named setting; they are not claims of independent trials or distinct outputs.

## Controls and limits

All **1,664 settings** encrypt and recover an 87-rune prescribed sequence exactly. A second control places ciphertext F at three fixed positions, including two consecutive markers. Every setting reconstructs that ciphertext after decoding and re-encrypting. The two policies produce different control plaintexts, confirming that the test exercises the clock distinction.

An independent checker calculates alphabet choices from the number of earlier F/non-F symbols rather than using the producer's state machine. It reproduces every comparison and the digest of every decoded head.

These controls establish that the specified decoder is reversible and the census is reproducible. They do not establish that Cicada used these rules. Other keys, alphabet permutations, interruption runes, resets, noninitial starts and plaintexts remain outside the test. This is a **newly specified baseline** for an underdefined proposal, not a reproduction of a historical solver's exact cipher.

## Reproduce

The downloadable bundle includes the input text layers, frozen plan, results and both programs. Extract it without flattening folders, then run:

```text
python experiments/records/alternating-alphabet-interruption-clocks/run.py --check
python experiments/records/alternating-alphabet-interruption-clocks/check.py
python experiments/records/alternating-alphabet-interruption-clocks/plot.py --check
```

Python 3.9 or later is sufficient; no model, network access or external library is needed. The target settings were frozen before the census. Input-consistency checks and explicit assertions of the forced-marker clock states were added after the census during review. They change no cipher setting, comparison or saved result.
