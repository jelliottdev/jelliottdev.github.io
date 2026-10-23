# Distant key reuse and ciphertext autokeys

**Finding.** Two related source searches find no LP2 score at their declared **+30** pass line. The highest whole-lag scores are **+7.05** for a repeated-key relation and **+5.30** when an earlier ciphertext rune serves as the key. The strongest shorter-stretch scores are higher, but still below +30. These are bounded screens of particular pair laws, not a rejection of every autokey or repeated-key cipher.

![Best whole-lag and stretch scores for both source models, all below the source pass line.](experiments/records/wulfic-lag-reuse-models/comparison.svg)

## The idea behind the test

If ciphertext is formed by adding plaintext and a key modulo 29, and the same key rune is used again after a gap of **L** runes, subtracting the two ciphertext runes cancels the key. This gives a testable relation between rune pairs **L** places apart. The source's **AC** search also tries shifted or reflected key relations. Its **AD** search asks whether an earlier *ciphertext* rune itself supplied the later key, in forward or reverse order. Both are more specific than searching for a high count of repeated runes.

For every forward gap from 11 through 12,945 in the continuous 12,956-rune LP2 text, the programs score all allowed pair relations and 29 shifts. They also inspect reverse pairings where two positions have a fixed sum. **F** measures evidence over an entire forward diagonal, as a long periodic key would require. **S** finds the best contiguous stretch on a forward or reverse diagonal, as a shorter reused piece would require. The test uses a solved-LP1 rune-frequency model and scores complete declared diagonals or stretches, rather than selecting words that look promising.

| Source model | Best whole gap F | Best forward stretch S | Best reverse stretch S |
| --- | ---: | ---: | ---: |
| AC · repeated key relation | +7.05 | +19.86 | +18.23 |
| AD · ciphertext as key | +5.30 | +22.49 | +23.16 |

The source fixed **+30** as a positive screen and **−10** as an exclusion only where planted controls establish enough power. Four flat anti-doublet null streams per model had to stay below +30 for a valid run. The original control grids reproduced exactly: AC's periodic tests support exclusions only through gap **12,500**, and its planted reused stretches all pass only at **3,000** runes; AD's corresponding figures are **12,900** and **200**. Shorter, different or more elaborate key reuse remains outside those calibrated exclusions.

The top AD whole-gap score comes from lag **12,942**, leaving only **14 rune pairs**. With the source's largest possible per-pair emission ratio, even its theoretical ceiling is **+17.41**. It cannot meet +30 under any such key. The table preserves the source's maximum, but it is not a near-hit from a fully testable long diagonal.

## A source-code repair that matters

The pinned AC and AD programs each encounter the same one-row array error during their planted-stretch controls, in both quick and full modes. The source helper allocates 29 rows even when the caller passes a single shift. We changed that allocation to the actual row count **in memory only**, leaving the pinned checkout untouched. After that correction, all **138 AC** and **184 AD** original control rows match the published tables exactly. The full source scans and output formatting remain unchanged; the replay checks every row of all six published source tables before accepting the finding. This is an **amended-source replay**, not an unchanged execution of a program that currently crashes.

The independently checked input is Liberpedia's page text: its LP2-00–55 GP29 rune sequence matches the source's 12,956 positions exactly. A separate checker rebuilds the pair-law score tables and recomputes sampled whole-gap and forward/reverse-stretch values from that sequence, including the leading source results.

## Inspect or reproduce

- [AC lag table](experiments/records/wulfic-lag-reuse-models/source-stage_ac_lags.tsv), [top scores](experiments/records/wulfic-lag-reuse-models/source-stage_ac_top.tsv), [controls](experiments/records/wulfic-lag-reuse-models/source-stage_ac_controls.tsv).
- [AD lag table](experiments/records/wulfic-lag-reuse-models/source-stage_ad_lags.tsv), [top scores](experiments/records/wulfic-lag-reuse-models/source-stage_ad_top.tsv), [controls](experiments/records/wulfic-lag-reuse-models/source-stage_ad_controls.tsv).
- [Exact rune numbers](experiments/records/wulfic-lag-reuse-models/source-stream.bin), [frequency model](experiments/records/wulfic-lag-reuse-models/source-model.json), [result summary](experiments/records/wulfic-lag-reuse-models/results.json), and [scope plan](experiments/records/wulfic-lag-reuse-models/plan.json).

Run `python experiments/records/wulfic-lag-reuse-models/check.py` for the independent source/site and sampled numerical checks. With the [pinned upstream checkout](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c), run `python experiments/records/wulfic-lag-reuse-models/replay_source.py --source PATH --output PATH` to repeat the full amended-source screens and check all six generated TSV files against the archived tables. NumPy is required. Use an output directory separate from the checkout.

The test does not consider word resets, other pair laws, keys that change between spans, a different language model, or a later decoding layer. A finding below +30 does not mean every one of those possibilities was tried.
