# Wulfic legacy methods: internal grouped queue

Pinned source: [`Wulfic/Cicada3301-Liber_Primus` at `bf89d3d`](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy). The machine-readable [queue](wulfic-legacy-method-groups-2026-10-23.json) lists **all 107 archived Python scripts**, each with its exact repository path, Git blob, first source docstring line, literal file/page references, closest site records, and remaining work. The generator checks that every local source file is byte-identical to its pinned Git blob. This was a static source review; it ran no manuscript tests and certifies none of the old results.

The scripts fall into **22 provisional method/dependency groups**, not 107 independent ideas. Many files are alternative hillclimbers, saved-key viewers, monitors, word segmenters, or crib refiners downstream of a selected candidate. File triage counts are 40 open optimizer/related scripts, 35 partially overlapping, 16 dependent on unverified inputs or selected keys, nine in two finite candidate groups, three utilities, three replayed adaptations, and one exact source replay with a separately labeled diagnostic. Those counts classify *files*, and should never appear as a count of completed experiments.

## Best next grouped checks

| Group | Source anchor | Gate before an experiment |
| --- | --- | --- |
| Prime/keyword streams | `prime_stream_solver.py`, `keyword_stepped_stream.py`, `p21_30_keyword_sweep.py` | Crosswalk their complete key and offset grids against the already replayed `combined_cipher_test.py`; correct old page identities, then batch only the distinct operators with one whole-search control. |
| Periodic word cribs | `period_crib_solve.py` plus crib validators | Pin the source's page/period combinations and dictionary. Require held-out words or a whole-search control: a self-selected fitting crib is not a reading. |
| Shared-key/two-time-pad | `twotime_crib.py`, `twotime_pad_analysis.py`, `ttp_crib_drag.py` | Verify the asserted identical ciphertext spans on the corrected pages *before* accepting the shared-key premise; freeze pair alignment and crib grid. |
| Feedback and autokey | `autokey_comprehensive.py`, `p21_30_autokey_solver.py`, `stream_cipher_attack.py` | Deduplicate exact feedback clocks, resets, skip rules and phases against existing autokey records; plant a solved-text control. |
| Transposition and rearrangement | `transposition_solver.py` and four P21–30 variants | Separate invertible column/route rules from arbitrary word rearrangement, then test a finite key/route grid with round-trip checks. |

The existing ADFGVX, combined keyword/prime, singleton-LFSR, and Deor records cover **their declared finite scopes**, not their entire neighboring groups. The Deor source's zero hits came from impossible raw-score thresholds; the recorded normalized analysis is a separate diagnostic. Source labels such as “page 20” use an old folder numbering: pinned `page_20` is current LP2-03. Each proposed replay still needs a source-specific input check and a success rule fixed before scoring.

## Why the rest is queued differently

The P02, P24, P25, anchored and GPU hillclimbers form connected optimizer lineages. Their downstream scripts inspect candidate outputs selected by earlier searches. Before replay, recover a pinned checkpoint, original target bytes, score/training data, complete stopping/selection rule, and independent control. Key-validation scripts cannot verify a claimed plaintext if they rely on the same assumed anchors that generated it. Source code comments calling a result “verified” or “breakthrough” are claims to examine, not adopted evidence.

The upstream [legacy README](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md) warns that older rune/image pairings and moved relative paths make the historical outputs unreliable. The site-to-source page mapping is independently recorded in `research/source-intake/wulfic-legacy-page-map-2026-10-23.json`; it validates the *current pinned files*, not every earlier run.
