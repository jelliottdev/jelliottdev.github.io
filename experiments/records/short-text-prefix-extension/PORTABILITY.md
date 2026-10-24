# Reproduce the short-text prefix scan

Use Python 3.12 and NumPy 2.5.4, installed separately. Commands below start at the extracted bundle root. Nothing installs packages or downloads inputs automatically. External corpus texts and normalized corpus arrays are not bundled.

Prepare the exact 94 files plus manuscript from a local checkout containing Dukotah revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`, plus the separately obtained exact KJV file. Every raw hash, normalized array hash, membership and order must match the frozen input manifest. Git lazy fetching and authentication prompts are disabled.

```sh
python experiments/records/short-text-prefix-extension/reproduction/portable.py setup --git /path/to/cicada3301 --kjv-file /path/to/exact-kjv.txt --destination /path/to/new-c01-inputs
python experiments/records/short-text-prefix-extension/reproduction/portable.py verify --inputs /path/to/new-c01-inputs
python experiments/records/short-text-prefix-extension/replay.py --inputs /path/to/new-c01-inputs
```

Alternatively supply an already prepared directory with the exact manifest paths. The reused adapter also offers explicit `--download-kjv` instead of `--kjv-file`; that network option was not exercised for this extension and accepts only matching bytes. No alternate edition is substituted.

Replay stages the frozen producer in a temporary directory, reruns all 37 controls and both separate prefix calls, and compares every deterministic report and all 40,245 floating/integer score pairs. It then runs the separate independent parser/counter against every target alignment. Only runtime durations are ignored. Original expectations remain untouched. A successful run reports no complete real-prefix match, maxima 87/400 and 37/120, and successful equality checks.

For a quick saved-evidence check that requires no external input files:

```sh
python experiments/records/short-text-prefix-extension/check.py
```

The saved merged-context receipt compares the six exact pattern arrays with the earlier replay and combines its 84-text maxima with the new rows. It does not rerun those earlier alignments. Recreating that contextual merge additionally requires the earlier record’s bundle and `independent/merge_context.py`; the primary replay and independent new-target check do not require it.

The retained source code is MIT, copyright 2026 Dukotah; see `reproduction/source/LICENSE`. Individual third-party corpus rights are separate. The manifest and publication assessment preserve exact source URLs and input provenance. The test concerns word-length compatibility, not plaintext recovery or a calibrated global probability.
