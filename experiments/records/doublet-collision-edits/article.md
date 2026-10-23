# Removing or splitting adjacent repeats

**Result.** Three fixed edits all suppress adjacent repeats when applied as a final operation to the archived LP2-00–55 rune stream. They do **not** reveal which edit, if any, was used to make that stream. Both insertion rules can also give the same output from different inputs, even if the decoder knows the input length. A reverse-edit step therefore needs extra information that the proposal did not supply.

![The original stream has 86 adjacent repeats. Deleting the later rune leaves none; inserting fixed F leaves eight; inserting a different rune leaves none.](experiments/records/doublet-collision-edits/collision-edits.svg)

The supplied list proposed deleting one copy of a repeat (`ABBC → ABC`) or splitting it with a filler (`ABBC → ABDBC`). We pinned one complete pass for each, plus a deliberately stronger insertion control. They are three **variants of one collision-edit idea**, not three independent LP2 decryptions.

| Forward edit on LP2-00–55 | Runes afterward | Adjacent repeats afterward |
| --- | ---: | ---: |
| Original archive | 12,956 | 86 |
| Collapse each run to its first rune | 12,870 | 0 |
| Put `F` between each original repeat | 13,042 | 8 |
| Put the next GP rune between each original repeat | 13,042 | 0 |

The eight repeats left by fixed `F` insertion occur where the original repeated rune is itself `F`; an `F` inserted between two `F`s does not separate them. Choosing a filler guaranteed to differ from the repeated rune removes that edge case, but this adaptive choice was **our control rule**, not a specified historical key. These are forward edits to an already sparse ciphertext. Reaching zero doublets by editing it says little about how its original 86 arose.

## Why undoing an edit is harder

The deletion rule loses positions. For instance, the three four-rune strings `FFFTH`, `FFTH TH` and `FTH TH TH` (spaces here only separate GP rune labels) all collapse to `FTH`. Knowing there were four runes does not choose among them.

Insertion can also be ambiguous, even with a declared filler. Under the fixed-`F` rule, `TH F TH TH` and `TH TH F TH` both become `TH F TH F TH`. Exhaustive enumeration over the small alphabet `{F, U, TH}`, holding original length fixed, first finds **two** ambiguous outputs among length-four originals for each insertion rule. That toy result proves these fixed transforms are not generally one-to-one; it does not estimate how many LP2 readings they permit. The [complete preimage counts](experiments/records/doublet-collision-edits/results.json) cover original lengths one through five.

The source example also mentions moving a repeated rune (`ABBC → ABCB`), but it does not say how to handle the end of a stream, runs longer than two, or new collisions. We have not turned that open rule into an invented test. Likewise, the filler glyph, the stage at which editing happens, and a decoder's removal clock were not fixed in the source.

## Exact scope and next test

We filtered the [archived LP2 page texts](#/reader/lp2-00) to GP runes and edited each of the 56 pages separately. Page breaks never become adjacent pairs. The [plan](experiments/records/doublet-collision-edits/plan.json) states the pass order and run handling; [results](experiments/records/doublet-collision-edits/results.json) give the before/after count on every page. The original supplied discussion is identified by its attachment SHA-256 in the plan.

A proposed LP2 decryption using one of these edits would need a frozen preceding cipher, filler or deletion-position rule, and a way to recover a planted known reading before scoring unsolved text. The [decoder controls](#/experiments/decoder-skip-controls) show why a plausible-looking output is not enough to establish exact recovery.

Run from the repository root or the experiment ZIP with Python 3.12 or later:

```text
python experiments/records/doublet-collision-edits/run.py --check
python experiments/records/doublet-collision-edits/check.py
python experiments/records/doublet-collision-edits/plot.py --check
```

The independent checker reconstructs edits by maximal equal-rune runs instead of the producer's adjacent-pair loop. It checks all page totals, input hashes, and toy preimage counts. Neither program treats a reduced doublet count as a plaintext reading.
