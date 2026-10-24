# Reproduce the payload-as-message search

Python 3.12 and its standard library are sufficient. No package installation, external transcription, training books, credentials or network access are required. The bundle contains the two exact 256-byte inputs and all source/model/control dependencies. Extract it with repository-relative folders intact; run from the extracted root.

Quick check of every declared file, saved source and normalized winning-output scores, terminal selections and control counts:

```sh
python experiments/records/payload-ciphertext-skip-replay/check.py
```

Complete controls and target replay into temporary files, followed by independent scalar reconstructions:

```sh
python experiments/records/payload-ciphertext-skip-replay/replay.py
```

The replay compares all deterministic fields exactly, excluding only elapsed seconds. Existing expected files remain untouched. It repeats 144 known-message controls and their wrong-key checks, 24 forced padding paths, 96 allocation checks, then the 96 payload target calls. It independently reconstructs the controls and every complete target beam. Recorded producer runtimes were about 40 seconds for controls and 13 seconds for targets, before independent audits; other computers may differ.

Expected results: 144 control scores pass, but only 137 recover the complete reading; all correct readings remain in their terminal beams. Wrong-key passes are zero. Target source and normalized diagnostic passes are both zero. This reproduces a historical algorithm measurement, not a rejection of messages in the payload.

All source bytes come from Dukotah/cicada3301 revision f08b20b632d91209ddbaa747e8e2f23df0c78ba1. The supplied source MIT license and frozen manifests identify attribution/hashes. The safe loader runs only section 1 key constructors and decoder definitions; it never executes the original file's other target sections. Source ranking, finite 356-symbol prefixes and appended zero padding remain unchanged. The independent target audit reconstructs all 96 beams and 27,062 ordered terminal hypotheses, without sampling.
