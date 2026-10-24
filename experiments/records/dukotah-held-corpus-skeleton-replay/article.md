No tested alignment matched the complete manuscript word-length pattern. With the exact-length rule, the best alignment agreed at **593 of 2,928 word positions**. Those positions meet the length rule; this does not recover the manuscript’s words or mean that 593 consecutive word lengths matched.

The scan used **84 eligible texts from 94 available files**. It is a replay of these exact archived inputs, **not the historical 224-text corpus** reported by the source. It does not establish a plaintext or exclude a language.

![Best full-pattern word-length counts, each out of 2,928 positions.](experiments/records/dukotah-held-corpus-skeleton-replay/length-matches.svg)

## What was compared

The [pinned source program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round10/L4-skeleton/run_scan.py) compares a sequence of manuscript word lengths with every eligible contiguous alignment in each text. The source parser takes its first 55 percent-separated manuscript segments, yielding 2,928 words. It splits words on dashes and periods and treats slash marks as line wraps. Corpus text passes through the source’s fixed Latin-to-rune-length normalization. This retains the archived input convention; it is not a fresh scan of every current page transcription.

Three full-pattern rules were tested: exact length; symmetric tolerance of one rune; and a directional interval from the observed length minus that word’s F-rune count up to the observed length. The latter models F runes that might be nulls. The source also tests the **first 400 and first 120 words** with the interval rule; it does not test every manuscript subwindow.

| Pattern | Best compatible positions | Shuffled-pattern maxima |
|---|---:|---|
| Full, exact | 593 / 2,928 | 586, 590, 583, 588 |
| Full, within one rune | 1,445 / 2,928 | 1,450, 1,445, 1,448, 1,448 |
| Full, F-count interval | 664 / 2,928 | 656, 662, 650, 659 |
| First 400, interval | 109 / 400 | 109, 109 |
| First 120, interval | 47 / 120 | 48, 50 |

Each number is a maximum after searching the same eligible texts and offsets. Four full-pattern shuffles and two shuffles per prefix are too few for a calibrated global probability or a claim that the real pattern is statistically equivalent to shuffled patterns. No such inference is made here.

## Exact coverage and controls

The unchanged scanner omits every text shorter than **2,928 words**, even when testing the shorter prefixes. Thus ten available files were omitted. The eligible files contain 9,799,472 normalized words and supply 9,553,604 unique full-pattern alignments, 9,765,956 first-400 alignments and 9,789,476 first-120 alignments. Shorter patterns are evaluated more than once near block joins; those repeated evaluations are not extra independent alignments.

Before the target scan, independent direct counts checked all three matchers at **103,995 synthetic offset values**, including block joins and tail plants. The source’s planted-text control then recovered two available passages at their exact text and offset: KJV and Emerson, each scoring 2,506/2,928 under exact matching and 2,928/2,928 under the interval rule. Only two eligible plant texts were available under its unchanged selection rule. Its single shuffled control does not establish the preregistered null-score gate, and the source’s separate corruption/degradation tests were not replayed. There is no measured bound on tolerance to other editions, insertions, deletions or changed word boundaries.

All 21 saved target winners were independently recounted with integer comparisons. The full corpus maxima were not independently searched a second time; the saved per-text summaries have membership, bounds and near-integer checks. This replay does not cover reordered or noncontiguous plaintext, other encodings, unavailable corpus texts, or changed input conventions.

## Saved results and reproduction

The [saved scan](experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/scan_results.json) retains every pattern’s global winner and per-text maximum. The [independent witness audit](experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/independent-target-audit.json) records integer winner counts and omissions. These let readers inspect the reported maxima without repeating the corpus search.

The reproduction bundle includes exact MIT-licensed source code, frozen plans, input hashes and receipts, but **no corpus texts or derived length arrays**. [Portable reproduction instructions](experiments/records/dukotah-held-corpus-skeleton-replay/PORTABILITY.md) give the exact bundle-root setup, T0 control, manuscript scan and expected-output comparison commands. Every raw and normalized input must match before a full replay can run. Adapter checks confirmed all 94 normalized arrays against the original loader and bit-identical synthetic scanner outputs; they did not rerun the manuscript search.

For a quick audit without the corpus scans, this separate command validates saved bytes and arithmetic only:

```text
python experiments/records/dukotah-held-corpus-skeleton-replay/check.py --check
```
