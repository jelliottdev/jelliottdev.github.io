## Finding

**A straightforward rail-fence reading does not stand out in this bounded test.** Across LP2-00–55, the best of nine rail counts matched **70** words in a fixed English list. The same nine-way search on page-rotated controls had a median of **78** matches; **195 of 199** controls matched at least 70. The unchanged rune order matched 57. These are dictionary matches, not a translation.

![The best rail-fence word count is below the median of the alignment controls.](experiments/records/rail-fence-visible-words/comparison.svg)

## The proposal and the actual test

[TheronEagle's public rail-fence script](https://github.com/TheronEagle/liber-primus-research/blob/a6c5d13f7591030367daace993c887af20a5e0ab/experiments/2026-09-24/rail_fence_test.py) decrypts each page using two through ten rails and scores the resulting letters as words in a dictionary. Its saved result names two rails as the highest scorer. The repository points to an absolute local path for its word list and another for its transcription; neither file is part of that repository. Its numeric result therefore cannot be exactly replayed from its published checkout.

Here the input is Liberpedia's pinned LP2-00–55 rune text: **12,956 runes** arranged into **2,776 visible word slots**. As in the source code, a hyphen ends a slot; line-break marks and punctuation do not. The [fixed 369,652-word list](experiments/records/rail-fence-visible-words/lexicon.txt) is derived from the [Unlicense English-words repository](https://github.com/dwyl/english-words/blob/20f5cc9b3f0ccc8ce45d814c532b7c2031bba31c/words_alpha.txt), with the exact transform and source hash in [SOURCE.txt](experiments/records/rail-fence-visible-words/SOURCE.txt). A decoded slot counts only when its exact GP Latin transliteration is in that list. The denominator includes short slots that cannot score, so the counts should be compared only under this same scoring rule.

| Reading | Matched slots |
| --- | ---: |
| Printed order, no rail transform | 57 |
| Two, four, or nine rails | 70 each |
| Median of 199 control maxima | 78 |

Each control rotates the rune stream of *each page* by a seeded, nonzero offset, keeps its visible word lengths, tests all nine rail counts, and retains the best score. The page's rune inventory and contiguous ciphertext order remain intact; the rotation changes the alignment with word slots. This comparison asks whether the printed alignment of the proposed rail reading is better than the same method applied at other alignments. It is not a model of how Cicada composed the manuscript. The saved control maximum scores range from **67 to 90**. The complete nine-rail counts and all 199 control maxima are in [results.json](experiments/records/rail-fence-visible-words/results.json).

## What this does and does not exclude

The decoder was checked two ways: the main script encrypts an actual solved-page rune sequence and recovers it at each rail count, while the separate checker recomputes all manuscript outputs through a different index permutation. This rules out a broken rail inverse as the explanation for the ordinary score.

The test covers **only** conventional page-by-page rail-fence decryption with two through ten rails, this word segmentation, this GP transliteration and this fixed dictionary. It says nothing about keyed columns, a rail count outside the range, combining pages, moving word boundaries, a preceding substitution layer, or a non-English plaintext. In particular, the source repository's wider statement that all transpositions are ruled out does not follow from these nine cases.

To reproduce offline, use the experiment ZIP and run `python experiments/records/rail-fence-visible-words/run.py --check`, followed by `python experiments/records/rail-fence-visible-words/check.py`. Both need Python 3 and the archived source files; no network call is made during the run.
