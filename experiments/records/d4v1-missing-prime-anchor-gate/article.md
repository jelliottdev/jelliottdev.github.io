# Missing-prime keys and routes: checking the score

**Result.** A pinned C++ search looks for three consecutive words whose rune-prime sums point to the 2013 missing-prime list. Only then does it try two repeating keys and several routes. Its final screen asks whether a candidate has rune frequencies like solved pages. On one known 157-rune reading, **all 199 shuffled controls passed that screen for each key** after the source's 29 Atbash shifts. Reordering runes cannot change this frequency score at all. These controls do not support treating a score above the source's threshold as a recovered reading.

![Both source keys pass all 199 shuffled controls; changing a route cannot change the unigram score.](experiments/records/d4v1-missing-prime-anchor-gate/control-screen.svg)

| What we checked | What happened |
| --- | --- |
| Three consecutive synthetic words with prime sums 73, 79 and 83 | The source trigger fired once. Inserting one nonmatching word stopped it. |
| The 256-pair key and the 180 missing-prime key | Both recovered a deliberately encrypted known reading. After shuffling the ciphertext, **199/199** controls for each key still exceeded the source's strict 0.91 score threshold at some Atbash shift. |
| Column, diagonal and inward-spiral routes at widths 3 and 7 | All six inverse-constructed examples recovered the reading. Every route preserves the same rune counts, so its score is unchanged for a fixed shift. All **199/199** shuffled route controls exceeded the source's strict 0.90 threshold. |

The test uses **one known reading that contributed to the source's solved-page frequency target**. These plants check the operator and the trigger; they do not estimate performance on other English passages. The shuffled texts are controls, not alternative proposed decipherments. We did **not** count anchor sequences on unsolved pages or run a manuscript decryption here. A later test needs a fixed reading-sensitive score and a full-search control before it can say whether these keys or routes help.

## Source and transcription

The [pinned program](https://github.com/d4v1-sudo/my_cicada_tools_cpp/blob/6bba820aed72184837611a82c79c4587157080aa/src/utils.cpp) uses the 180 primes from 73 through 1223. Those match the archived **2013 telnet-command gap**, which is distinct from CicadaOS `prime_echo`. Its 256-pair source key is spelled exactly like the current LP2-49–51 transcription. The same program's `pages.h` differs from its `secrets.cpp` at five letter-case cells. Those five disagreements and the still-uncertain glyphs are documented in [the grid transcription comparison](#/experiments/grid-radix-reconciliation) and [stem review](#/experiments/grid-stem-uncertainty). This check preserves the source's `secrets.cpp` key without silently correcting it.

The source and current site agree on the rune order of all 56 mapped LP2 pages. Punctuation changes word boundaries on LP2-04, LP2-21 and LP2-41, so any future count of three-word anchors must name which transcription it uses. The exact-source version uses the pinned `pages.h` text. No target-page result is reported here.

## Reproduce

The [frozen pretarget plan](experiments/records/d4v1-missing-prime-anchor-gate/plan-frozen.json), [control-calibration amendment](experiments/records/d4v1-missing-prime-anchor-gate/calibration-amendment.json), [source-derived fixture](experiments/records/d4v1-missing-prime-anchor-gate/fixture.json) and [all 199 control maxima](experiments/records/d4v1-missing-prime-anchor-gate/results.json) are included. Run `python experiments/records/d4v1-missing-prime-anchor-gate/run.py --check`, then `check.py` and `plot.py --check`. The independent checker recomputes both full shift searches and verifies six route plants. The optional [C++ fixture](experiments/records/d4v1-missing-prime-anchor-gate/source-controls.cpp) can be compiled against the pinned upstream source to confirm its tokenizer, trigger and key transforms; upstream code is linked by revision and hash rather than bundled.
