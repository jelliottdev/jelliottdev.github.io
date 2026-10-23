# Prime and keyword streams in three archived searches

Could a familiar word, a reordered prime list, or a word-controlled walk through primes decode these LP2 pages? Three archived scripts ask related questions. We replayed their complete finite grids together on verified page text. **The source screens do not establish a complete reading.** One prime-stream IoC peak is unusual against this small control set, so it remains a lead to inspect rather than a solved page.

![Observed maximum IoC for each source search against 49 complete shuffled searches](experiments/records/wulfic-prime-keyword-stream-families/comparison.svg)

| Source method | What it tried | What happened |
| --- | --- | --- |
| Repeating keywords | 18 named words, three directions, ten pages | None of 540 outputs made every one-rune word an I or A. The best IoC was 1.119, reached or exceeded in 18 of 49 shuffled searches. |
| Prime streams | Sequential and five alternate prime orders; three key forms, three directions, and the source's F-skip rule on eight pages | Nine sequential settings passed at least one permissive source screen. The highest IoC was 1.174 on LP2-09; one of 49 shuffled searches reached it. This output missed all six one-rune word checks and its inspected opening is not a coherent passage. |
| Keyword-stepped primes | 20 literal keyword arrays, eight prime-index rules, offsets 0–1000, three directions, eleven pages | Of 5,285,280 settings, 2,270 passed the source's all-singleton I/A gate. None reached its IoC > 1.3 hit threshold. The highest gated IoC was 1.281; 12 of 49 shuffled searches reached it. |

These are **three source methods**, not millions of separate experiments. The control repeats each entire search after shuffling rune order *within each page*, so the comparison includes the choice of its best setting. A shuffled page preserves length and rune frequencies, but not word structure or a realistic encryption process. Forty-nine controls give only a coarse reference, especially for a rare peak. An IoC peak or a short accidental word is not a decryption.

## What was actually replayed

The archived programs call pages `page_21`, `page_28`, and so forth. Those map to current **LP2-04** and **LP2-11** by subtracting 17; the archive's page bytes and rune counts were checked against the current page text before scoring. The source's word-boundary parsers differ slightly, so each branch keeps its own one-rune positions. The programs' relocated file paths are broken in the archived checkout; this replay uses the verified pinned input bytes and preserves the source operations and scoring screens.

The first script repeats 18 parsed keywords. Its optional `data/verified_keys.json` branch was left out: that exact path is absent from the pinned Git tree. An archived file with the same basename exists elsewhere in the tree, but the script does not load it and its provenance was not assumed. The prime script uses 80 valid sequential offsets plus five named nonsequential generators; its listed offset 5000 cannot hold a page in the source's 5,133-prime table. Its `gp_ext` stream repeats sequential offset zero, so it is an output alias. The stepped script searches all 20 literal arrays and all eight source generators. Some `keyword_add_sequential` settings already occur in the earlier [combined keyword-and-prime test](#/experiments/wulfic-keyword-prime-layer-grid): 17,600 source settings share those exact arrays, offsets, signs, and pages. That overlap is recorded, not counted as a new idea.

The highest prime IoC comes from adding a totient-based sequential stream starting at prime index 110 on LP2-09. Its IoC is 1.174, quick word score is 9, and **zero of six** source one-rune word positions become I or A. The script's top *retained* candidate is different because it ranks permissive screen hits by a combined heuristic. Neither output is a documented reading. Further work would need a fixed rule that predicts a longer passage or an untouched page, not a higher score selected from another flexible grid.

## Check and reproduce

Each branch passed a synthetic arithmetic control: a planted GP29 stream with I/A at all one-rune positions was encrypted under one declared setting, then recovered exactly and crossed the source hit threshold. This checks that the operations can detect that artificial pattern; it does not establish power to recognize English. We also compared sampled key streams, decodes, and keyword parsing with functions extracted from the pinned source revision. An independent scalar checker reconstructs every saved page winner and its full decoded-output hash.

The [result table](experiments/records/wulfic-prime-keyword-stream-families/results.json), [frozen plan](experiments/records/wulfic-prime-keyword-stream-families/plan.json), and [input snapshot](experiments/records/wulfic-prime-keyword-stream-families/inputs.json) specify the exact pages, keys, counts, null seed, and source revision. Run `python experiments/records/wulfic-prime-keyword-stream-families/check.py` for the independent checks. Run `python experiments/records/wulfic-prime-keyword-stream-families/run.py --check` to repeat all three complete grids and 49 controls. The optional `source_parity.py` additionally requires a checkout of the pinned upstream commit.

This bounded replay covers those exact old source settings and selected LP2 pages. It does not exclude different keywords, prime orderings, resets, pages, or cipher families.
