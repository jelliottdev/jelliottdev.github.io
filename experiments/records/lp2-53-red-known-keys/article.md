## Result

**Neither of the two documented LP1 Vigenère keys made LP2-53’s red passage read like the archived English examples.** The best of 42 key/phase/sign settings scored **−6.69**, below the fixed **−5.5** English threshold. Its score was ordinary among matched controls: **460 of 999** shuffled red passages had an equal or higher *best-of-42* score. This is a bounded test of two keys on this passage, not a finding about every possible key or plaintext language.

![The best red-passage score is near the center of shuffled-control maxima and below the scores of nine known readings.](experiments/records/lp2-53-red-known-keys/scores.svg)

## What was tested

The original page changes from black to red at the **last rune of line 6**. That rune and all runes on lines 7–9 make **51 red runes**, page rune positions **128–178** when counting from zero. The archived transcription has 179 runes in total. Hyphens separate words and slashes mark line layout; the red word lengths are **5, 4, 4, 11, 2, 3, 2, 6, 5, 5, 2, 2**. In particular, the leading hyphen on the last line separates its first two runes from the preceding word.

The two keys are the rune-index sequences documented for the **Welcome** and **second koan** readings. For each key we tried every starting phase and both arithmetic directions, calculating `Pᵢ = Cᵢ ± Kᵢ (mod 29)`. Only runes advance the key; punctuation and line breaks do not. Because every phase is included, resetting the key at the red start adds no new candidate. There is no internal full stop in the red span, so a full-stop pause also adds no new candidate. This leaves **42 distinct named settings**.

We scored each result with the site's pinned English quadgram model, applying it to canonical GP transliteration. Higher values look more like that model's English training text. The controls were run before scoring the manuscript: all **nine** archived solved-reading excerpts of the same 51-rune length passed the −5.5 threshold and beat all **200** of their own seeded rune shuffles. When those nine excerpts were enciphered with one of the two keys, their true plaintext ranked first in the same 42-setting search **nine times out of nine**. These controls show that this narrow test can recognize similar plaintext if either declared key is correct; they do not prove that every valid LP2 reading must score as English.

For a family-wise comparison, we shuffled the red rune order 999 times, preserving its rune counts. Each shuffle went through the **whole 42-setting search**, and we compared its best score with the manuscript's best. This controls for choosing the nicest-looking key after seeing all 42 outputs under that shuffle model. It is not a model of the unknown encryption process.

## Reproduce and limits

The [plan](experiments/records/lp2-53-red-known-keys/plan.json) pins the page image, transcription, alphabet, two-key source and scorer. Run `python experiments/records/lp2-53-red-known-keys/controls.py` to verify the quality gate, `python experiments/records/lp2-53-red-known-keys/run.py --check` to recompute all candidates and shuffles, and `python experiments/records/lp2-53-red-known-keys/check.py` for an independent reconstruction. [All 42 outputs and 999 control maxima](experiments/records/lp2-53-red-known-keys/results.json) are saved.

Other keys, position-dependent schedules, interrupts, transpositions, alternate rune mappings and non-English or nonstandard plaintext remain open. The visible red passage could also have a role other than a separately encrypted English sentence.
