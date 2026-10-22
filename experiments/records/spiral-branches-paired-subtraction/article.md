## What is being tested?

The Spirals and Branches text, followed by the nine-rune heading before the Möbius number panel, contains 2,883 runes. Spiral Branches also has 2,883 runes after its 125 F runes are removed. A source discussion suggested pairing the streams, reversing Branches like a musical retrograde, or applying Atbash before modular subtraction. We test five *specified* ways to do that pairing and ask whether the best output has unusually high whole-stream index of coincidence (IoC) relative to two controls.

This is a new computation of suggestions in that discussion, not a replay of a reported successful decryption. The two long runic strings pasted in the supplied source thread match the archived Spirals and Branches-plus-heading transcriptions exactly: 1,145 and 1,738 runes, respectively. Their hashes are fixed in the [plan](experiments/records/spiral-branches-paired-subtraction/plan.json). The second 2,883-rune stream is rebuilt from LP2-40–53 after removing every F; the discussion did not supply a complete scored sweep of it.

## Inputs and five variants

Use zero-based positions in the 29-rune alphabet. Let **A** be the 1,145 Spirals runes, then the 1,729 Branches runes, then the nine-rune pre-Möbius heading. Let **B** be the 3,008 Spiral Branches runes after deleting its 125 F runes. Retain all other headings. Punctuation, page breaks and the number panel are not rune positions. At every aligned position output `(B − A) mod 29`.

| Variant | What changes in A |
| --- | --- |
| Direct | Nothing; printed order. |
| Reverse Branches | Reverse its 1,729 runes; leave the nine-rune heading at the end. |
| Reverse tail | Reverse Branches and the heading together as one 1,738-rune block. |
| Atbash Branches | Replace each Branches index `x` by `28 − x`; leave the heading unchanged. |
| Atbash tail | Atbash the entire Branches-plus-heading block. |

The two reverse and two Atbash treatments make the thread's “Branches” versus “Branches + Table” boundary ambiguity explicit. A head-of-Spirals-to-tail-of-Branches pairing is covered by reversal of the relevant tail. We do not search starts, other page ranges, arbitrary offsets, keys, multiplication, XOR, or different F handling.

## Score and controls

For each complete output, count ordered pairs of identical runes and divide by `2,883 × 2,882 = 8,308,806`. This is whole-stream IoC, not a language score. The chosen statistic is the **largest** of the five variant scores. Each control repeats all five variants and takes its own maximum:

1. **Every nonzero circular shift of B:** 2,882 comparisons preserve its rune sequence and frequencies but change its alignment with A. The observed unshifted alignment is the remaining position.
2. **999 within-page shuffles of B:** each LP2-40–53 non-F page chunk is independently shuffled, preserving its size and rune counts. These disrupt local order while retaining page-level composition. The pseudorandom seed is recorded in the plan.

These controls ask whether the observed *alignment* stands out under their respective assumptions. They do not estimate how rarely a researcher might discover some equal-length sections and some promising operation after searching many alternatives.

## Result

| Variant | Ordered equal-rune pairs | IoC |
| --- | ---: | ---: |
| Direct | 286,654 | 0.034500 |
| Reverse Branches | 286,132 | 0.034437 |
| Reverse tail | **287,504** | **0.034602** |
| Atbash Branches | 286,138 | 0.034438 |
| Atbash tail | 286,280 | 0.034455 |

Reverse tail is the best of the five on this measure. But 921 of the 2,882 nonzero circular shifts reach at least its score; including the observed alignment gives **922/2,883 ≈ 0.320**. Similarly, 341 of 999 within-page shuffles reach it; the usual add-one estimate is **342/1,000 = 0.342**. The selected score is ordinary under both comparisons. Neither number is a probability that the full historical idea is correct or incorrect.

![Two horizontal box plots show the best-of-five score inside both control distributions.](experiments/records/spiral-branches-paired-subtraction/score-controls.svg)

The boxes span each control's middle half, their central lines mark medians, and the whiskers reach the saved minimum and maximum. The dashed line is the observed 287,504. The figure displays the distribution of the **maximum over five** for every control input, not the distribution of a single selected variant. [Download the figure](experiments/records/spiral-branches-paired-subtraction/score-controls.svg), [all candidate streams and source coordinates](experiments/records/spiral-branches-paired-subtraction/candidate-streams.json), or [the complete results and control scores](experiments/records/spiral-branches-paired-subtraction/results.json).

## Reproduce and interpret

From a full checkout or the [experiment ZIP](downloads/experiments/spiral-branches-paired-subtraction.zip), run:

```text
python experiments/records/spiral-branches-paired-subtraction/run.py --check
python experiments/records/spiral-branches-paired-subtraction/check.py
python experiments/records/spiral-branches-paired-subtraction/plot.py --check
```

The first command rebuilds all five outputs, 2,882 shifted maxima and 999 shuffled maxima. The independent checker verifies each stored source coordinate against the archived text, all 14,415 output runes by re-encryption, every observed score through direct rune-pair comparison, sampled controls and both complete tail counts. The [source-bound section-count guide](#/wiki/section-rune-counts) checks the 2,883 construction separately. The [reported-attempt entry](#/wiki/reported-attempts?section=spirals-branches-2883-alignment) identifies the supplied discussion without republishing its full transcript.

This result does **not support an unusual IoC peak** for the five subtraction variants and exact representation above. It does not test n-gram scores, additions, multiplication, XOR, periodic IoC, alternative page spans, partial readings or different interruption rules. Even a high whole-stream IoC would need a complete, stable reading and a prediction on text not used to choose its operation. Keep a later variant as a separate test with its own search scope and controls.
