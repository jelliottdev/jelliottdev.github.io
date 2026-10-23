# Word boundaries as key clocks

These three archived search branches ask whether the visible separators and words control a shifting key. We replayed the exact source rules on all 55 rune-bearing unsolved LP2 pages, then compared each branch's best score with **49 shuffled searches that repeated the entire branch**. None of the manuscript bests crossed the source's fixed −5 English quadgram threshold. The highest score from any branch, −6.897, was matched or exceeded by 44 of the 49 shuffled *combined* searches.

![Three short bars show the number of shuffled searches that reached or exceeded each manuscript score. A note shows that the archived known-page candidate matches 56 of 85 runes, then diverges.](experiments/records/dukotah-word-boundary-key-clocks/comparison.svg)

| Source branch | What moves the key | Best unsolved score | Shuffled searches at least as high |
| --- | --- | ---: | ---: |
| FH1 · separator clock | A chosen `-`, `.`, or `/` advances the stream without printing a rune | −6.904, LP2-14 | 23/49 |
| FH3 · punctuation reset | A selected word, clause, line, or segment mark restarts the stream | −7.008, LP2-51 | 43/49 |
| W1–W5 · word sums | GP-prime values of the previous word, or the previous rune, supply the next key value | −6.897, LP2-49 | 37/49 |

**The known-reading check changes how to read this result.** The archived FH3 report highlights an `AN END WITHIN THE DEEP WEB...` opening on source page 55 (LP2-56). We compared its *entire* 85-rune output with the documented reading. The first 56 positions match; rune 57 differs, and the full text is **not** recovered. That candidate scores −5.282, below the source's own −5 threshold. A plausible opening is therefore not a passed known-page control. Seven synthetic examples did recover the complete known Parable reading when encrypted with these exact rules; they check the implementation, but they cannot show that the original ciphertext uses any of them.

## What was searched

FH1 used the source's three separator sets and four subtractive streams: primes, primes minus one, totients, and the repeating `DIVINITY` key. FH3 used four reset marks and three streams. The five word-sum variants used the 29-value Gematria Primus prime map. W1 uses the previous *ciphertext* word's prime sum, W2 the previous *decoded* word's sum, W3 the cumulative ciphertext-word sums, W4 the totient of the previous ciphertext-word sum, and W5 the previous ciphertext rune's prime value. Every W variant included both signs and both Atbash states, with a zero initial key. In the source parser, **any non-rune ends a word**.

That is 660 FH1 outputs, 660 FH3 outputs, and 1,100 word-sum outputs across the 55 unsolved source segments. The source omits the rune-free LP2-50 transcription segment. We checked the rune sequence of every other source segment against its site page. Source FH2 is a first-rune shift subset of the separately tested [whole-page affine family](#/experiments/wholepage-affine-gp29), so its archived winner is checked for source parity but not counted again here. FH4's proposed file relocation was not an executed cipher search.

The score is the archived mean English quadgram log score on the GP transliteration; a higher number means more English-like **under that model**, not a readable solution. The shuffled comparison preserves each page's rune inventory and every punctuation position. It repeats the full choice of stream, separator or word rule, sign, Atbash setting, and page before retaining the maximum. It measures selection effects under that shuffle, not the probability of a cipher model.

## What remains open

These results do not exclude a different initial state, a key from earlier pages, other separator meanings, a different language model, or a model that predicts the original punctuation. A new proposal can improve on this replay by fixing its key-clock rule before looking at the target page and recovering a complete known passage plus an untouched LP2 passage. The original 56-rune prefix should not be treated as a complete positive control.

## Reproduce and inspect

The [experiment plan](experiments/records/dukotah-word-boundary-key-clocks/plan.json) fixes the source revision, grid, controls, and exclusions. [Results](experiments/records/dukotah-word-boundary-key-clocks/results.json) contain every shuffle maximum and the exact source winners. The [replay](experiments/records/dukotah-word-boundary-key-clocks/run.py) checks the pinned programs and saved results; the [independent checker](experiments/records/dukotah-word-boundary-key-clocks/check.py) reconstructs all manuscript settings and shuffle maxima without importing those programs. Run:

```text
python experiments/records/dukotah-word-boundary-key-clocks/run.py --check
python experiments/records/dukotah-word-boundary-key-clocks/check.py
python experiments/records/dukotah-word-boundary-key-clocks/plot.py --check
```

The source scripts and their archived outputs are preserved under `source/` at commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. The 49 full-grid shuffle controls and the full-reading comparison are **our added tests**, not results claimed by the archive. See the pinned [false-holes source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/false_holes.py) and [word-sum source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/wordsum_selfkey.py).
