## Result

**Neither documented LP1 key produced an English-like complete page in this search.** We decoded all **55 rune-bearing pages from LP2-00–55** with the Welcome and second-koan keys, both arithmetic directions and every key phase: **2,310 complete-page outputs**. None reached the fixed −5.5 score that recognized the archived readings. The highest score was **−6.675**, on LP2-55 with the Welcome key.

That best result was not unusual after allowing the search to choose among all 2,310 outputs: **68 of 199** shuffled-page controls scored at least as high under the same entire search. This comparison does not exclude other keys or forms of Vigenère.

![The LP2 best score sits within the full-search shuffle range, well below the weakest archived English control.](experiments/records/wholepage-known-vigenere-keys/scores.svg)

## Why this is a different test

The earlier [known-key opening test](#/experiments/lp2-known-vigenere-keys) asked whether a page *began* with one of nine exact twelve-rune readings. A page could fail that test yet still contain English elsewhere. Here the score uses **every rune on each page**, including headings. Punctuation and line breaks do not advance the repeating key; each page starts a fresh phase. LP2-50 has no runes and therefore contributes no candidate. The shortest tested page has 66 runes.

We first checked whether the scorer could recognize texts of that minimum length. All **nine** archived 66-rune reading excerpts cleared the fixed threshold and beat all 200 of their own rune-order shuffles. When each excerpt was enciphered with one declared key, its true plaintext ranked first among the same 42 key/phase/sign settings **nine times out of nine**. Those controls establish sensitivity to similar known plaintext; they cannot show that every valid LP2 reading must resemble the English training corpus.

For each of 199 null trials, we shuffled rune positions **separately within every page**, preserving each page's length and rune counts. We then tried all 42 settings on all 55 pages and kept only that trial's highest score. This is a comparison against the entire chosen search, not 2,310 individual unadjusted comparisons. A shuffle is a positional control, not a model of the unknown cipher.

## Reproduce and limits

The [frozen plan](experiments/records/wholepage-known-vigenere-keys/plan.json) pins the page transcriptions, nine reading traces, keys and quadgram model by SHA-256. The [results](experiments/records/wholepage-known-vigenere-keys/results.json) contain every candidate score and output hash, the nine controls and all 199 global null maxima. Run `python experiments/records/wholepage-known-vigenere-keys/run.py --check`, then `python experiments/records/wholepage-known-vigenere-keys/check.py` for an independent reconstruction. The [plot script](experiments/records/wholepage-known-vigenere-keys/plot.py) regenerates the figure.

The test assumes the archived GP rune order, direct repeating-key addition or subtraction, a page-level reset, one of **two** known keys, and English-like output under the pinned scorer. It does not test key interruption, other keys, transposition, cross-page state, a hidden intermediate layer, or another language. It provides no decryption of the unsolved pages.
