# Positional totient shifts on complete LP2 pages

**Result.** None of the 5,500 complete-page outputs from the 100 fixed positional totient offsets reached the predeclared English score line. The best was LP2-55 at offset 64 (−6.60); 87 of 199 full-search shuffled controls did at least as well. Nine known readings passed the English scorer; all nine deliberately encrypted controls were decoded exactly and ranked their true offset first, so this is a useful bounded screen of this particular rule. It does **not** identify or exclude a general totient cipher.

![The best LP2 output sits below the known readings and among full-search shuffled controls.](experiments/records/d4v1-positional-totient-streams/summary.svg)

The tested rule is simple: number the runes from zero at the start of each page, compute Euler's totient of the position plus an offset, and subtract that number modulo 29. For example, offset 17 starts with shifts φ(17), φ(18), φ(19), and so on. The [pinned source code](https://github.com/d4v1-sudo/my_cicada_tools_cpp/blob/6bba820aed72184837611a82c79c4587157080aa/src/utils.cpp) tries offsets 0–99. Our new screen retained that operator and range, then used an independently pinned English quadgram score and a complete-search shuffle comparison. It is **not** a claim that the author ran this English scoring test.

| What was checked | Outcome |
| --- | --- |
| LP2-00–55, excluding the number-only LP2-50 | 55 rune-bearing pages × 100 offsets = 5,500 outputs |
| Fixed English line | Zero outputs reached −5.5; best −6.60 |
| Nine archived complete readings | All nine reached the line and beat all 199 own shuffles |
| Nine known readings encrypted with offset 17 | All nine recovered exactly and ranked offset 17 first |
| 199 pagewise shuffle trials, each searching every offset and page | 87 trials equaled or exceeded the actual global best; plus-one tail 88/200 |

The [original source's positional hit rule](experiments/records/d4v1-positional-totient-streams/source-positional.json) differs from this English test: it requires both a within-page offset z-score above 3.5 **and** a solved-rune unigram fitness above 0.90. A post-target audit found no source-rule LP2 hit, but its plant gate triggered for only seven of nine known readings; 41 of 199 complete-search shuffles produced at least one hit. The source unigram target was built from known solutions, so this plant check is in-sample. Therefore the source rule's zero is not a powered exclusion. The 0.85 threshold in that source belongs to a separate current-word branch, not this positional branch. The [dated correction](experiments/records/d4v1-positional-totient-streams/plan-amendment.json) preserves the original frozen plan and states this source-rule distinction; the 0.85 diagnostic is limited to 1,000 random strings of one length.

The source's other option-29 rule derives a shift from the GP-prime sum of the **current ciphertext word**. That input-dependent word rule did not pass a complete-reading plant check and remains unresolved; it is not included in the 5,500 outputs. An exploratory known-warning preimage check found words for which the proposed plaintext has no ciphertext preimage under the simple same-word interpretation, and the source handles some separators differently when advancing its word clock. A faithful replay needs to preserve that clock and establish a working positive control first.

This screen uses the archived GP29 rune streams, including headings, and scores the canonical GP Latin rendering as English. The source page numbers 17–72 align with LP2-00–55 after normalizing the J-rune glyph spelling; LP2-50 has no runes in the pinned transcription. Other offsets, signs, separator rules, languages, key layers and different totient constructions remain untested here.

## Reproduce

Download the experiment files and run `python experiments/records/d4v1-positional-totient-streams/run.py --check`, then `check.py`, `source_gate.py`, `source_positional.py`, and `plot.py --check` from the repository root. The [frozen plan](experiments/records/d4v1-positional-totient-streams/plan.json) pins all page, reading and scorer inputs; the [complete result](experiments/records/d4v1-positional-totient-streams/results.json) includes per-page winners and all 199 null maxima. `check.py` independently reconstructs the 5,500 outputs and all shuffled searches. Python with NumPy and Numba is required; no upstream source code or network fetch is needed for these checks.
