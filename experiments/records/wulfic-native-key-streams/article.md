# Do Cicada's own numbers work as a key?

**No setting crossed the reading threshold, but the short keys leave whole-section claims inconclusive.** We replayed [Wulfic's Stage I](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_i.py) and [Stage M](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_m.py) from one pinned source revision. Their **5,742 recorded settings** test prime numbers, values derived from solved LP1 text, and three readings of the LP2 number grid. None reaches the program's **+30 reading threshold**. Both complete tables reproduce the published source files byte-for-byte.

![Six source keys: each LP2 score stays below the reading threshold, while planted key controls are higher.](experiments/records/wulfic-native-key-streams/comparison.svg)

The blue point for each key is its best LP2 score on an alignment of at least 100 runes. Gray shows the range from 20 planted encryptions under that **same key and detector**. Control texts have different lengths because the source keys do.

## What was actually tried

Stage I starts at the beginning of three streams: consecutive primes; one Gematria sum per solved LP1 word; or the prime value of each solved LP1 rune. Stage M starts at the beginning of three streams read from the printed 256-cell grid: its base-60 bytes, their regrouped five-bit values, or the individual base-60 digits. The grid streams contain **256, 409 and 512 values**, respectively. The [independent checker](experiments/records/wulfic-native-key-streams/check.py) confirms that the source's grid tokens match Liberpedia's 256 transcribed tokens, then constructs all three numeric streams from those tokens.

For each key, the source applies three arithmetic directions and 29 shifts. Stage I scores nine manuscript sections separately and as one joined stream; Stage M also tests positions immediately after and ending at the grid. The detector tolerates occasional skipped or repeated key steps and scores whether decrypted rune frequencies resemble known LP1 text. Its key starts at **position zero**. These are six source-defined streams under one decoder, not a general search of possible Cicada-derived keys.

**Key length matters here.** Once the detector runs off the end of a key, later runes contribute a neutral score. In particular, Stage M's long-page result mostly measures what its first few hundred grid-derived values do, not a complete-page decryption. Stage I's LP1 word-sum stream likewise has only 726 values. The highest LP2 score in either complete table is from the **nine-rune** section 10 (+4.83), far too short to carry a strong reading. Among alignments of at least 100 runes, the best scores are **−65.54** for Stage I and **−13.75** for Stage M.

## Did the detector have enough power?

After inspecting the source results, we added a **supplemental diagnostic**. It plants each exact key in 20 anti-doublet encryptions, using text lengths that fit within the key: **729, 650 and 729 runes** for the three Stage I keys, and **230, 368 and 460** for the grid keys. **All 120 planted scores pass +30; none of the 120 wrong-key scores does.** This shows the detector can recognize these keys within those bounded lengths. Because the diagnostic was designed after the LP2 replay, it is a power check, **not** a preregistered source control or a correction for selecting a promising key after the fact. The [plan](experiments/records/wulfic-native-key-streams/plan.json) and [control table](experiments/records/wulfic-native-key-streams/supplemental-controls.tsv) state its exact rules and values.

This excludes no alternate start position, repeated grid key, other base-60 reading, different plaintext model or cipher. Stage I also performs a separate **nine-rune square-title vocabulary check**; it is not part of these stream scores and deserves its own treatment if used as evidence.

## Reproduce

From the repository root, run `python experiments/records/wulfic-native-key-streams/run.py --check`, `python experiments/records/wulfic-native-key-streams/check.py` and `python experiments/records/wulfic-native-key-streams/plot.py --check`. The bundled [candidate tables](experiments/records/wulfic-native-key-streams/results.json) and controls are hashed in the record. To rerun the historical programs, check out the [source repository](https://github.com/Wulfic/Cicada3301-Liber_Primus) at commit `bf89d3d13aad2b8f2c95ab195cf1b092f250775c` and run `python experiments/records/wulfic-native-key-streams/replay_source.py --source-dir PATH_TO_CLONE`. The wrapper writes into a temporary directory and checks both full output tables byte-for-byte. Run `calibrate.py --source-dir PATH_TO_CLONE --check` to repeat our supplemental diagnostic.
