# Do line or word lengths carry a message?

**Question.** Could the number of runes on each physical line, or in each visible word, be read as another GP-rune stream?

**Result.** The direct readings tested here do not stand out. The highest English score came from taking each visible word's rune count, subtracting one, and reading the resulting GP index without joining four-letter groups across pages. It scored **−6.697**. In **78 of 256** matched shuffles, the *best* of the same eight readings scored at least that high (global add-one estimate **79/257 ≈ 0.307**). This does not produce a deciphered passage.

![The first six word lengths become GP symbols; the best observed English score lies near the middle of the shuffled-search range.](experiments/records/layout-count-streams/count-stream.svg)

## What the counts mean

The 55 rune-bearing LP2-00–55 pages contain **594 physical lines** and **2,776 visible word slots** under the stated transcription rules. A line contributes its number of GP runes; a word slot is a hyphen-delimited group after removing slash layout marks. Punctuation is not counted. LP2-50 has no transcribed runes and contributes neither lines nor words.

For example, the first six word lengths on LP2-00 are **8, 9, 3, 3, 11, 5**. Under the best tested mapping, subtracting one gives indices **7, 8, 2, 2, 10, 4**, whose canonical GP Latin labels are **W H TH TH I R**. We tested both the count itself and count minus one, with either page-local or joined scoring, for lines and words: **eight readings** in all. Every reading cleared the predeclared minimum of 100 English four-letter groups.

Each control shuffles the observed counts **within every page**, preserving how many lines or words each page has and the counts on that page. The same shuffled arrays are reused across all eight readings in a trial. We compare the best observed score with the *best of all eight* in each control, so choosing the attractive mapping after seeing its score is included in the comparison. The observed score falls comfortably inside that control range. Eight synthetic controls with known decoded GP readings planted into count streams recovered the intended indices exactly and passed the English-recognition gate; they check that the mapping and scorer can detect a direct reading.

This tests **direct English from ordered counts** with these two elementary GP-index mappings. It does not rule out another number encoding, a key applied to the count stream, a different word-boundary convention, or a message in a visual layout layer absent from the transcription. The [source catalog](research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt) proposes layout counts as an idea; it does not document a specific historical attempt.

## Inspect and reproduce

[`results.json`](experiments/records/layout-count-streams/results.json) records every count, observed score and shuffled-search score. Run `python experiments/records/layout-count-streams/run.py --check` and `python experiments/records/layout-count-streams/check.py` from the repository root. The second program parses the page JSON independently of the producer's text-file parser and recomputes all eight observed scores and all 256 complete control searches.
