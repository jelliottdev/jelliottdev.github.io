# Does the preserved Emerson text work as an LP2 running key?

Under **one fully specified additive rule**, the tested LP2 pages do not show a convincing Emerson-key opening or continuation. We searched every **43,325 contiguous offsets** of the archived *Self-Reliance* extract for each of LP2-00, LP2-31 and LP2-54. The best 96-rune openings score near maxima from eight complete searches using shuffled versions of the same source letters. Their next 96 runes remain far below a planted known-reading control. This does not exclude other running-key rules, source editions, alphabets or page positions.

![Opening and held-out continuation scores for Emerson and shuffled-source searches](experiments/records/emerson-running-key/search-scores.svg)

## Why this source and what rule was frozen

Emerson's *Self-Reliance* is a documented source for a **2014 book-coordinate cipher**, reproduced separately in the [historical control](#/experiments/emerson-book-cipher-control). That history makes it a concrete candidate to test; a coordinate cipher does not establish a running key for LP2. We used the site's preserved **50-paragraph PDF derivative**, not an authenticated creator edition. Its original file, extraction convention and SHA-256 are described in the [Emerson source guide](#/wiki/emerson-self-reliance).

Join the 50 stored paragraphs with spaces, uppercase, and retain ASCII A–Z. The result has **43,516 letters**. Map A to 0 through Z to 25. For each LP2 page, take its first 192 archived alphabet runes in order, including headings. At each offset, subtract successive source-letter values from rune indices modulo 29; the source does not wrap, and punctuation advances neither stream. This is deliberately a Latin-letter-to-rune numeric key, not a claim that Emerson's prose was written in Gematria Primus.

Score the first **96 decoded runes** after concatenating their canonical Latin labels. The score is the mean base-10 log probability of overlapping four-letter groups under the pinned [English quadgram model](#/experiments/english-scorer-controls); unseen groups receive count 0.01. Select the highest first-window score, breaking ties toward the lowest source offset. Only then score the **next 96 runes** at that same offset. Search eight deterministic full-stream letter shuffles with exactly the same offset budget and selection rule. Those controls preserve the source's letter counts while breaking its order. The [plan](experiments/records/emerson-running-key/plan.json) fixes these choices and hashes every input.

## Complete search maxima

Higher scores are more English-like under this exact scorer. The shuffle ranges below contain the **best selected candidate from each complete shuffled-source search**, not scores of arbitrary unselected offsets.

| Target | Best Emerson offset | First 96 | Eight shuffle maxima | Next 96 at chosen offset | Shuffle continuations |
| --- | ---: | ---: | ---: | ---: | ---: |
| LP2-00 | 19,692 | −6.364 | −6.372 to −6.143 | −7.575 | −7.807 to −7.054 |
| LP2-31 | 1,162 | −6.353 | −6.444 to −6.218 | −7.368 | −7.875 to −7.306 |
| LP2-54 | 21,646 | −6.462 | −6.536 to −6.255 | −6.817 | −7.754 to −6.997 |

The LP2-54 continuation scores higher than all eight shuffled-source continuations. That observation is retained, not dismissed: there are only eight controls, its first window was not stronger than their maxima, and its continuation score is still far below the known-reading plant. These values are **descriptive**, not a calibrated p-value or an English-language decision threshold. The [full result](experiments/records/emerson-running-key/results.json) preserves the top five offsets and both decoded windows for every search, so a reader can inspect the candidate text rather than rely on one number.

## Did the search have a fair chance to find a real key?

As a positive control, take the first 192 **decoded** rune indices of LP1-06, add the same Emerson key beginning at zero-based offset **3,301**, and search the resulting synthetic ciphertext without telling the search its offset. The complete 43,325-offset search ranks **3,301 first**, recovers the known indices exactly there, and scores **−4.096** on the first 96 and **−3.883** on the next 96. This proves the pipeline can recover a planted instance of the specified rule at this length. It does not establish its power for every possible plaintext or source text.

The scorer itself has documented language limits: it can reject meaningful Welsh, for example, while accepting some non-English text. Canonical rune labels also differ from ordinary English spelling. A low score therefore cannot exclude a non-English plaintext or every English representation. The result only weakens this **single Emerson / A–Z shifts / subtractive modulo-29 / page-opening** variant. A proposal with a different source conversion, offset reset, interrupted clock, or selected passage is a different search and must count those choices.

## Reproduce

With Python 3 standard library, from the repository root or extracted [experiment ZIP](downloads/experiments/emerson-running-key.zip):

```text
python experiments/records/emerson-running-key/run.py --check
python experiments/records/emerson-running-key/check.py
python experiments/records/emerson-running-key/plot.py --check
```

The producer checks all source hashes and replays every complete offset search. The independent checker reconstructs the source, shuffles, rune streams and planted ciphertext; it scores by counted quadgrams rather than the producer's sliding sum, and verifies every maximum, top-five list and holdout. The plotter checks the published figure. No API, model download or network call is needed.
