# Pinned Wulfic source-method inventory

Source: [`Wulfic/Cicada3301-Liber_Primus` at `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c). This is an internal execution queue, not a count of independent puzzle ideas or proof of the source's conclusions. The local pinned checkout contains the code, canonical text, corpora, OutGuess files, and published result TSVs. Source code has no LICENSE in the checked tree; do not vendor it into Liberpedia. Each replay must preserve its own controls and exclusion rules.

| Stage | Source method | Shared engine / grouping | Liberpedia state |
| --- | --- | --- | --- |
| AA | Keyless sliding-context cipher repeat invariant, widths and n-grams | Deterministic-local-output invariants with Z | Published `wulfic-local-codebook-invariants`; five source TSVs byte-identical with Z |
| AB | Shared position alphabet restarting at section, paragraph, clause, line or page | Restart models with AF | Published `wulfic-stage-ab-reset-alphabets` |
| AC | Arbitrary-lag key reuse with diff/sum/sumrev pair scores | Long-lag key relations with AD/AE | Blocked: pinned source `--quick` crashes in `segment_stats` when a one-row control table is supplied; no LP2 replay claim |
| AD | LP2 ciphertext reused as its own key, forward and reversed diagonals | Long-lag key relations with AC/AE | Same source quick-control crash as AC; no LP2 replay claim |
| AE | Periodic key through arbitrary alphabets, equality at every continuous-stream lag | Long-lag key relations with AC/AD | Exact replay draft `wulfic-periodic-alphabet-lags`; two source TSVs byte-identical |
| AF | Restarting position key plus a distinct constant unit shift | Restart models with AB | Published `wulfic-stage-af-unit-shifts` |
| AG | Base-29 digits of seven constants and three concatenated number sequences | Drift-tolerant key streams with AH | Published `wulfic-number-key-streams` |
| AH | Six arithmetic functions, each raw and cumulative mod 29 | Drift-tolerant key streams with AG | Published `wulfic-number-key-streams` |
| I | Part 1: primes and solved-LP1 value streams. Part 2: nine-rune square-title vocabulary check | Part 1 with M; Part 2 separate short-crib evidence | Part 1 published `wulfic-native-key-streams`; Part 2 exact replay draft `wulfic-square-title-vocabulary`, 30 full-heading cases and source random-key control reproduced |
| M | Three grid-byte/digit representations as a finite GP29 key | Fixed-start drift-tolerant key streams with I | Published `wulfic-native-key-streams` |
| N | Decode the 256 grid bytes under LP-native keys; printable/signature and rune-score screens | Grid-byte decoders with X/Y, but distinct success screens | Exact replay draft `wulfic-grid-native-keys`; 456 source settings byte-identical |
| R | 25 Cicada number/payload sources, two mappings, cyclic unknown phase, 43,500 source settings | Cyclic-phase key streams; related detector to AG/AH/I/M | Unreplayed exact source; controls available; costly full grid |
| S | Named long-key values used as position-specific substitution alphabets | Alphabet families with W | Upstream run explicitly void; exact source replay not recorded |
| T | Flatness bound for many-class position alphabets, gated simulation | Alphabet distribution family with U/V | Exact replay draft `wulfic-position-alphabet-flatness-bound`; 45 source rows byte-identical, independent manuscript statistics and pooled boundary verified |
| U | Quagmire random-alphabet relabellings and χ² mixture | Alphabet distribution family with T/V | Exact replay draft `wulfic-quagmire-random-alphabets`; all 80 source rows byte-identical with pinned result, 20 powered exclusions and four untestable settings; independent manuscript and verdict checks |
| V | Named keyword alphabets and labeled unigram likelihood | Alphabet distribution family with T/U | Unreplayed exact source |
| W | Long named byte keys as random position alphabets; corrected flat negative controls | Alphabet families with S | Exact replay draft `wulfic-position-alphabet-long-keys`; full 505-control gate valid, 12/50 powered exclusions, 38 untestable; both W tables byte-identical with pinned published outputs |
| X | Grid-byte key-free structure, periodic byte-bijection invariant, integer and decompression screens | Grid-byte structure with N/Y; avoid duplicating existing direct-byte checks | X2 exact source-component replay draft `wulfic-grid-periodic-byte-invariant`: full 100,000-null, source control windows and all 256 reading/period rows; X1/X3/X4 remain unexecuted here, and X1/X4 partly overlap site direct-byte records |
| Y | Grid under every on-disk long byte source, four routes and four arithmetic operations | Grid-byte decoders with N/X | Unreplayed exact source; likely large grid |
| Z | Deterministic word and aligned block codebooks, repeat invariant after anti-doublet redraw | Deterministic-local-output invariants with AA | Published `wulfic-local-codebook-invariants`; five source TSVs byte-identical with AA |

The already published Liberpedia records in adjacent areas do **not** automatically replay these source-specific models. For example, general periodic-affine and grid-header records use different controls from AE and X. Conversely, Stage I's short-title vocabulary exercise must not be counted as covered by the Part 1 stream replay.

Remaining useful coverage: AC/AD need an explicitly documented upstream bug fix or source correction before any historical replay. Stage I Part 2's title-vocabulary exercise remains separate. Stage S/W and T/U/V have distinct source gates; R/Y require runtime checks before their large grids. Stage X1/X3/X4 need overlap reconciliation before another public record. This is a workload recommendation, not a claim that any unrun source is valid or invalid.
