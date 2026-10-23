# The red passage on LP2-53

**Question.** Does the long red passage have the equality pattern expected of an ordinary solved-text passage after a simple rune substitution, and does it differ from the black text on the same page?

**Result.** Its 51 runes have an index of coincidence (IoC) of **0.0298** and **26 distinct runes**. None of **2,492** same-length windows from eight archived decoded GP passages is that flat: their lowest IoC is **0.0400** and they use at most 23 distinct runes. But the red result lies *inside* the **0.0259–0.0408** IoC range of 78 black-text windows on LP2-53. Color distinguishes the passage visually; these measurements do not establish a separate cipher.

![The red span compared with matched solved and same-page black windows.](experiments/records/lp2-53-red-equality-invariants/equality-profile.svg)

## The exact span

The original [LP2-53 image](images/lp2-53.jpg) shows a red **ᛏ** as the final rune of text line 6, then three complete red lines. In the archived transcription these are page rune ordinals **128–178**, inclusive: **1 + 24 + 22 + 4 = 51** runes. Punctuation, line slashes, the final dotted mark and artwork do not enter the count. This span is shared with the separately documented LP2-53 key tests; this record asks a different, key-free question.

## Why equality is useful here

A one-to-one substitution can rename runes, but it cannot change which positions are equal. Thus IoC, number of distinct runes and adjacent-equal pairs are **invariants** of every bijective monoalphabetic substitution. We used the `output_index` traces from eight known GP readings, excluding LP2-56’s hash-target passage, and slid a 51-rune window within each reading. These windows overlap; the counts describe the archived corpus and are not independent samples or a probability that the manuscript was produced by a cipher.

The red span has **zero adjacent equal pairs**. That alone is not surprising: every black-window control on the same page also has zero, and **2,155 of 10,000** shuffles of the red runes (21.55%) likewise have none. Shuffling keeps the red symbol counts and IoC unchanged while testing whether their observed order has an unusual immediate-repeat count.

The red span’s much lower IoC than the decoded passages makes a direct one-to-one renaming of those *particular* known-reading-style windows a poor account of its equality structure. It does **not** eliminate simple substitution of another plaintext with different statistics, nor more complex ciphers or section-specific treatment. The same-page black comparison is the clearest limit on calling the red color a separate encryption layer.

Run `python experiments/records/lp2-53-red-equality-invariants/run.py --check` and `python experiments/records/lp2-53-red-equality-invariants/check.py` from the repository root. The independent checker reads the page text rather than the page JSON, rebuilds all reading windows, verifies the image hash and 51-rune span, tests substitution invariance with a planted rune permutation, and repeats all 10,000 conditional shuffles. Exact inputs and results are retained with the record.
