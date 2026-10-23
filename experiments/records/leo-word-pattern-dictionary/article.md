# Do short LP2 words resemble shifted dictionary words?

## Finding

The [published word-pattern test](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/tests2.py) reproduces from its pinned inputs. A Caesar-shifted dictionary word has the same sequence of differences between neighboring runes. Among LP2 words of four through eight runes, Caesar-pattern matches are **165/511, 12/317, 0/256, 0/216 and 0/156**. The 2,000 random rune words sampled at each length yield **627, 45, 4, 0 and 0** matches. Longer LP2 words give no Caesar-pattern hits in this dictionary; short words alone are weak evidence because the dictionary covers many possible patterns.

Allowing any invertible affine multiplier raises the LP2 matches to **511, 166, 13, 1 and 0**. The matched random-word rates are very similar, especially for lengths four through six. The solved-page plaintext check has Caesar matches in **322 of 325** words at these lengths, confirming that the dictionary can recognize most known reading words under the same segmentation. These observations do not identify a cipher or rule out other vocabularies and word-boundary choices.

![Affine dictionary-pattern match rates for LP2 words and uniform-random rune words, grouped by word length. They are similar at each length.](experiments/records/leo-word-pattern-dictionary/word-patterns.svg)

## What was compared

We used the nine unsolved-section rune transcriptions and `dictionary_all-rune.txt` from [relikd/LiberPrayground at commit `719380e`](https://github.com/relikd/LiberPrayground/tree/719380ebee0523ad7f2fbf389c6f960d51bea5a4). Word separators follow that source; line wraps are ignored. The [plan](experiments/records/leo-word-pattern-dictionary/plan.json) pins SHA-256 hashes for all 18 section files and the 10.3 MB dictionary. The script checks those hashes before counting. It also repeats the original test's single seeded stream of 2,000 independent uniform-random words per length.

The source calls one column “reversed.” Its code reverses the **difference tuple**. Literal reversal of a word also changes the sign of each difference: `Δ(reverse(word)) = −reverse(Δ(word)) (mod 29)`. We retain the source's values for an exact replay and report literal reversed-word values separately in [results.json](experiments/records/leo-word-pattern-dictionary/results.json). This correction affects that column's interpretation, not the Caesar or affine findings.

## Reproduce

Fetch the pinned relikd revision above, then run `python experiments/records/leo-word-pattern-dictionary/run.py --source-root PATH --check` and `python experiments/records/leo-word-pattern-dictionary/check.py --source-root PATH`. `PATH` is its checkout directory, containing `pages/` and `data/dictionary_all-rune.txt`. The input files are linked and hash-checked but not redistributed here. The separate checker rebuilds the complete LP2 Caesar and affine counts using first-rune anchored offsets, checks source fingerprints and verifies the reversal identity. The seeded random and solved-text controls are recomputed by `run.py`; the checker compares their published counts. `plot.py` regenerates the figure from `results.json`.
