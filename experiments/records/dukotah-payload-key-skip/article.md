# Can the number-grid bytes act as a key when key positions are skipped?

**Finding.** We reran a published decoder that treats the 256 bytes derived from the LP2-49–51 number grid as a repeating key. It permits a key position to be skipped when that position would have repeated the previous ciphertext rune. Across **880 fixed page and key settings**, no output reached the program’s English-score bar. The best score was **−6.756 on LP2-15**, below its **−5.5** bar. A separate implementation reproduced every decoded path and score.

The decoder can recover a known message under these rules: when we encrypted the complete **85-rune LP2-56 reading** with each payload, sign and Atbash setting, it returned the exact reading in **16 of 16** planted cases. That makes the no-hit result informative for this fixed search, while leaving other key construction rules open.

![The sixteen planted known readings clear the source's English-score bar and recover exactly. The highest-scoring manuscript setting remains below the bar.](experiments/records/dukotah-payload-key-skip/comparison.svg)

| What entered the decoder | Complete known text recovered | Above the source score bar |
| --- | ---: | ---: |
| Planted 85-rune reading | **16/16** | **16/16** |
| Unsolved manuscript pages | Unknown | **0/880** |

The score rates how closely the continuous rune transliteration resembles English four-letter patterns. Passing it is a search screen, not proof of a correct reading. In the planted cases we also compared **every rune** with the known text. The best manuscript case starts `EAEASYDANGYEALT…`; isolated letter-like fragments are not a decoded passage.

## What was tried

The source provides **two distinct 256-byte readings** of the LP2-49–51 grid. Each was tested forward and backward. Every byte becomes its remainder modulo 29, producing four candidate key streams. For each stream, the program tried both addition directions, with and without Atbash, at key offset zero on each of the **55 rune-bearing pages LP2-00–55**. LP2-50 has no transcribed alphabet runes and is skipped. The grid is therefore **4 streams × 2 signs × 2 Atbash choices × 55 pages = 880 settings**.

At each rune the beam considers the next key value or as many as three extra advances. An advance is allowed only if each bypassed value would have made the preceding ciphertext rune repeat. It keeps the 320 highest-scoring paths and chooses a complete page output. The exact source script does **not** run the whole-book branch described in its introductory comment; this replay covers its executable page loop only.

The 55 source rune arrays match the corresponding Liberpedia page records exactly, including the page-number shift after rune-free LP2-50. The original program reproduces its preserved output: the winning setting is the first byte reading, subtraction, Atbash, LP2-15. Our separate scalar decoder agrees on **all 880 full-length paths**, not only that winner.

There is an important boundary on the key model. For pages longer than 256 runes, the source repeats the payload enough to cover the page’s initial length. Its beam then pads with **zero key values** if a hypothetical skip path runs beyond the allocated key array. We preserved that executable behavior. This result does not test an indefinitely repeating 256-byte stream for every possible skip path.

The source’s broader generic validation script also calls for an unrelated `mabinogion.txt` as a wrong-key check. That file is absent from the pinned repository, so the generic gate stops before its wrong-key condition. Its correct-key part recovers **212/212** planted runes; the **payload-specific** full-reading controls above pass independently. We do not report the incomplete generic gate as passed.

## Reproduce

The [plan frozen before the manuscript rerun](experiments/records/dukotah-payload-key-skip/plan-frozen.json) fixes the source revision, grid, bar and controls. The [per-setting results](experiments/records/dukotah-payload-key-skip/results.json) include page labels, scores and hashes of every complete decoded path. Run these from a Liberpedia checkout:

```text
python experiments/records/dukotah-payload-key-skip/run.py --check
python experiments/records/dukotah-payload-key-skip/check.py
```

The first command runs the [pinned Campaign XVIII source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign18_skip/payload_skip.py) in a temporary directory and compares its report with the preserved log. The second independently reconstructs all page arrays, scoring, 880 beam outputs and 16 complete-message controls. Exact source code and inputs are bundled under the source project’s MIT license. The result concerns **this payload-as-key rule**; it does not evaluate every key one could derive from the number grid or the other Campaign XVIII branches.
