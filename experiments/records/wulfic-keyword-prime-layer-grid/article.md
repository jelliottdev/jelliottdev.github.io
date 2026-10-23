# Keywords combined with a prime stream

Could a familiar keyword remove one layer of LP2 while a prime-derived stream removes another? An [archived public script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/combined_cipher_test.py) defined a finite version of that question. We ran its fixed settings on the corresponding manuscript pages with a known-reading control and a whole-search comparison.

**None of the 224,128 tested settings crossed the script's IoC screen of 1.40.** The best was 1.29 on LP2-32. A planted 515-rune known reading decoded completely and scored 1.72, so the test can detect that example made with its own rules. The control is longer than any target page and does not establish equal detection power on short pages. The highest LP2 score is not an unusual search peak under our page-shuffle comparison: 42 of 49 shuffles reached at least that value.

![The best LP2 IoC is 1.29, below the 1.40 source screen; a planted known reading scores 1.72.](experiments/records/wulfic-keyword-prime-layer-grid/comparison.svg)

## What the script tried

At each rune position, it adds or subtracts one of **16 fixed keyword sequences** and one of **103 second streams**, modulo 29. The second streams include ordinary primes, prime minus one, cumulative prime-minus-one values, a linear count and Fibonacci values. Both signs are tried for both components. Each setting starts again at the beginning of each page. The script used the index of coincidence (IoC), a measure of repeated symbols, to screen its outputs; a high IoC alone would not establish a reading.

The named keywords are CABAL, DIVINITY, ENCRYPTION, OBSCURA, ENCRYPT, SHADOWS, DEOR, TOTIENT, MOURNFUL, VOID, AETHEREAL, BUFFERS, CARNAL, ANALOG, MOBIUS and FORM. We use their [literal source rune vectors](experiments/records/wulfic-keyword-prime-layer-grid/keys.json). Those labels are not a separate spelling check: for example, the source’s AETHEREAL vector includes both TH and a following H. A conventional re-encoding of that word is a different setting.

The source calls its inputs pages 21–54. Those names came from an older file layout. A rune-by-rune length and SHA-256 check shows they are **current LP2-04–37**, in order. This correction matters: testing today's LP2-21–54 would test different text. Our [input-mapping amendment](experiments/records/wulfic-keyword-prime-layer-grid/input-mapping-amendment.json) preserves the initial mistaken plan and records that an exploratory run on the wrong range was discarded before this result. The saved result uses only the verified mapping.

## How to read the result

The result covers exactly the source's keyword arrays, 103 stream definitions, four sign choices and 34 matched pages. Its 1.40 line is a candidate screen, not a proof that all layered ciphers fail below it. We also shuffled runes *within each page* and repeated the entire search 49 times. Those controls preserve each page's rune frequencies, so they reveal how large a best score can appear after searching many settings. They do not simulate every possible cipher.

The archived script is explicitly marked untrusted by its own repository and has a broken old directory assumption. We reimplemented its finite arithmetic on verified inputs. That is a new bounded test of the archived proposal, not a claim that its original historical output was correct.

The [plan](experiments/records/wulfic-keyword-prime-layer-grid/plan.json), [saved measurements](experiments/records/wulfic-keyword-prime-layer-grid/results.json) and [reproduction script](experiments/records/wulfic-keyword-prime-layer-grid/check.py) give the exact settings. Run `python experiments/records/wulfic-keyword-prime-layer-grid/check.py` to repeat the full grid, input checks and shuffle controls.
