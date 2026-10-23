# A source-defined search for derived keys

Could a short Cicada-related seed produce the key stream for the unsolved Liber Primus pages? This replays Dukotah's pinned B04 search, with its fixed seed list, key generators, skip-aware decoder and score rule.

## Result

The planted message ranked **first among 1,385,600 settings**. On the manuscript, none of **6,224,000 short-text decodes** reached the source's −5.5 score bar. The 150 selected settings were also decoded on a whole page and the joined unsolved text; none cleared the bar there.

![The planted control clears the fixed score bar; the best LP2 scores in stages A through D remain below it.](experiments/records/dukotah-b04-full-source-replay/scores.svg)

Higher scores mean a closer match to the source's English quadgram model. The planted score was **−4.157**. The strongest manuscript score, **−5.885**, came from testing short page openings in stage C. On the full joined text, the best of the selected settings scored **−7.239**. These are scores under one model, not decoded English.

| Search stage | Text checked | Settings | Best score |
| --- | --- | ---: | ---: |
| A | First 120 joined runes | 1,385,600 | −6.185 |
| B | First 120, with ten key offsets | 1,290,240 | −6.129 |
| C | Starts of 55 nonempty source page segments | 3,548,160 | −5.885 |
| D | Full first page; full joined text | 150 on each | −6.654; −7.239 |

This finding applies to the **specific source dictionary and transforms**. It does not exclude other seeds, salts, key stretching, changing keys between pages, or different plaintext languages. The successful planted control tests recovery on 120 runes; it does not prove the scorer would recover every kind of full-length message.

## What the search did

The source generated candidate key streams from 2,165 seed entries using 16 generators, five ways to reduce bytes to runes in stage A, both addition signs, Atbash choices and forward or reversed key order. Its decoder allowed up to three key skips per rune and scored outputs with an English quadgram model. Stage B varied key offset for 504 core seeds. Stage C restarted those seeds at each source page segment and tested its first 100 runes or fewer. The source transcription has no runes for LP2-50, so that segment contributes no C test; the page image is not empty.

Stage D used the best 50 configurations from each earlier stage, sorted and deduplicated to 150. Each was tested on the 262-rune first page and the 12,956-rune joined stream. The 300 cells read no source-added zero padding. An equal-score tie changes one candidate at the first-page top-50 cutoff compared with the source archive, but the score sequence and reported best match. The full-stream top 50 matches the archive exactly.

There is a **key-continuity limit**: the source reverses the whole generated stream for reversed-key candidates, and stage D asks for a different stream length from stages A–C. A reversed candidate's 120-rune key prefix can therefore change when extended to a whole page. Stage D is a source-defined follow-up screen; those reversed paths should not be described as a seamless extension of the earlier key. A forward-key check did preserve its prefix.

## Reproduce and inspect

The downloadable experiment includes exact pinned source code and inputs, the ordered top-300 results and histograms for A–C, all 300 D cell records, and independent check receipts. Run `python experiments/records/dukotah-b04-full-source-replay/run.py --check` to verify the packaged bytes and arithmetic. `--quick` runs 1,280 synthetic source decodes offline. `--full --output DIR` repeats the G2 control and all A–D settings into an external directory; this takes many minutes.

The portable source adapter checks the original file hashes in place of the original Git-HEAD check. The three text files whose content forms seeds are copied exactly. Other book files supply only their **filenames** to this seed generator; the bundle preserves those names as empty placeholders, so the search needs no unrelated book contents. Stage D used an accelerated decoder representation with unchanged source rules. All 150 first-page results and four full-text cases chosen before Stage D ran were recomputed with the original decoder; their returned fields and key-read counts match exactly. The source's own [plan](experiments/records/dukotah-b04-full-source-replay/source/liber-primus/analysis/round13/B04/PREREG.md), [gate note](experiments/records/dukotah-b04-full-source-replay/source/liber-primus/analysis/round13/B04/GATE-NOTE.md), and [results](experiments/records/dukotah-b04-full-source-replay/source/liber-primus/analysis/round13/B04/RESULTS.md) are included for comparison.
