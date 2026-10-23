# Could earlier Cicada bytes select LP2's substitution alphabet?

One proposed way to use another file as a key is to let **each byte select a hidden rune alphabet**. The same byte selects the same alphabet whenever it returns. Wulfic's Stage W tests that model without guessing the alphabets: it asks whether runes under a repeated byte label show the repetitions expected of text. It checks five specified byte streams at every source phase, once for each of nine marked sections and once across the joined text of **LP2-00–55**.

**Finding:** the source's control gate passes. None of its **50 key/alignment settings** reaches the +30-nat detection threshold. **Twelve** have enough positive-control power to exclude this exact model; **38** are untestable, so their low LP2 scores do not count as exclusions. The best LP2 score is **+0.84**, using source byte file `page_17.bin` against the section covering **LP2-23–26**; that setting is untestable. No reading is produced.

![Stage W decisions for five key sources, ten alignments per source](experiments/records/wulfic-position-alphabet-long-keys/comparison.svg)

The figure's “Page 17/21/43” labels name [byte files in the source repository](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/data/outguess), **not** manuscript pages LP2-17/21/43. Their origin as puzzle payloads has not been independently verified here. The marked sections follow the [`$` boundaries in the source transcription](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/data/canonical/liber_primus_master.txt). We checked its rune sequence against Liberpedia's page text: all **56** LP2 pages match rune for rune. Relevant boundaries are: section 11, the last 150 runes of LP2-15 through LP2-22; section 12, LP2-23–26; and section 15, LP2-40–55. Section 10 contains only the first nine runes of LP2-15, so these sections are not always whole-page ranges.

| Source byte stream | Excluded alignments | Untestable |
| --- | --- | ---: |
| Wisdom hint | Joined LP2-00–55; LP2-40–55 | 8 |
| Wisdom hint, reversed | Joined LP2-00–55; LP2-40–55 | 8 |
| Source file `page_17.bin` | Joined LP2-00–55; LP2-40–55 | 8 |
| Source file `page_21.bin` | Joined LP2-00–55; LP2-15 (after first nine runes)–22; LP2-40–55 | 7 |
| Source file `page_43.bin` | Joined LP2-00–55; LP2-15 (after first nine runes)–22; LP2-40–55 | 7 |

These are **five source keys under one method**, evaluated at ten alignments. They are not fifty unrelated solving ideas. The [complete candidate table](experiments/records/wulfic-position-alphabet-long-keys/source-stage_w_candidates.tsv) gives every score, phase and verdict.

## Why the controls matter

The score uses rune repetitions within each byte-selected class. It averages a likelihood ratio over **all possible starting phases** of the named byte key; the best individual phase is shown separately in the table, but it is **not** the decision score. The source regards a mean score of at least **+30 nats** as a hit.

For each key and alignment, Stage W makes five synthetic messages encrypted by that exact kind of byte-selected alphabet and five flat negative messages made with an unrelated additive key. It also scores one LP2 stream against each shuffled key. If any flat negative or shuffled-key null reaches +30, the whole run is void. The highest such negative here is **+0.64**. A specific key/alignment is called excluded only if **all five** same-length positives reach +30 while LP2 does not. This is why the many short sections remain untestable, even though their LP2 scores are low. The [control table](experiments/records/wulfic-position-alphabet-long-keys/source-stage_w_controls.tsv) shows all **505** controls.

The earlier Stage S used the same LP2 score but its original negative-control design made that run void. We regenerated just the **50 Stage S LP2 scores** that Stage W requires. Each row matches the corresponding row in the pinned source's full 200-row Stage S table, and all 50 agree with the Stage W candidates. This numerical dependency does **not** revive Stage S's invalid conclusion; Stage W's own corrected controls decide what can be said here.

The result applies to these raw byte streams, their source-defined phase search and a key that stays in step. Skips, resets, another key source, a changing alphabet or an additional cipher layer are outside the tested model.

## Reproduce

From the Liberpedia repository root, Python's standard library checks the three bundled tables, recalculates all source verdicts and verifies the figure:

```text
python experiments/records/wulfic-position-alphabet-long-keys/run.py --check
python experiments/records/wulfic-position-alphabet-long-keys/plot.py --check
```

The [plan](experiments/records/wulfic-position-alphabet-long-keys/plan.json) pins the source revision, byte-file hashes, all settings and the decision rules. The two Stage W tables were regenerated with the unmodified [pinned Stage W program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_w.py) and match its published source files **byte-for-byte**. The Stage S subset was regenerated with the [pinned score function](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_s.py). To repeat the full calculation from a matching external checkout with NumPy:

```text
python experiments/records/wulfic-position-alphabet-long-keys/replay_source.py PATH_TO_WULFIC_CLONE
```

That wrapper verifies the pinned inputs, regenerates the Stage S dependency and the two Stage W tables in a temporary directory, then compares them byte-for-byte with the bundled files. The source code remains in its original repository.
