# Reproduce the archived-text word-length scan

Extract the experiment ZIP with its folders intact. **Run every command below from the extraction root**, the directory containing `experiments/` and `scripts/`. The same paths work from the repository root. Replace the example local paths with your own. Setup and scan output directories must not already exist.

## Environment and bundle check

The full replay uses Python 3.12 and **NumPy 2.5.4**, pinned in `experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/requirements.txt`. Git is needed only for local input setup. No model, paid API or hosted service is used.

In an extracted ZIP, verify the downloaded members first:

```text
python scripts/verify_bundle.py EXPERIMENT-dukotah-held-corpus-skeleton-replay-CONTENTS.json
```

The source code is pinned to [Dukotah/cicada3301 at f08b20b](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1). Exact source modules and their MIT license are included. Corpus texts and derived length arrays are **not** included; their individual redistribution rights are not inferred from the code license.

## Prepare exact external inputs

Use a local Git repository containing commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. Setup extracts the 93 selected tracked texts and the manuscript from its local Git objects. It does not modify that repository, clone it, or silently fetch missing objects.

Supply the separate KJV file locally. It must be **4,436,268 bytes**, SHA-256 `0f1a83cbcdc1d3fae6bcc3daaa496d4fa723fcce9526e84e20df12ae33fda986`:

```text
python experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/portable.py setup --git /path/to/local-cicada3301 --destination c01-inputs --kjv-file /path/to/exact-kjv.txt
```

Alternatively, replace `--kjv-file /path/to/exact-kjv.txt` with the explicit option `--download-kjv`. That requests only the previously recorded public URL `https://www.gutenberg.org/files/10/10-0.txt`. It rejects a changed hash, wrong size or redirect; it does not accept another edition as a substitute. This optional download was not exercised in the adapter checks.

Verify an existing or newly prepared input directory:

```text
python experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/portable.py verify --inputs c01-inputs
```

Expected totals are **94 texts, 9,808,699 normalized words, 84 eligible texts**. Verification checks all raw file hashes, normalized array hashes, loader membership/order and manuscript arrays. A missing, extra eligible or changed input fails before a scan. The source's 2,928-word minimum still omits ten texts even for its shorter prefix patterns.

## Run the source control and manuscript scan

These commands perform the actual corpus scans, using the unchanged source main functions. Run T0 before T1 and use fresh output directories:

```text
python experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/portable.py run --inputs c01-inputs --stage t0 --output c01-t0-output
python experiments/records/dukotah-held-corpus-skeleton-replay/reproduction/portable.py run --inputs c01-inputs --stage target --output c01-target-output
```

The first writes `c01-t0-output/positive_control_T0.json`; the second writes `c01-target-output/scan_results.json`. The recorded runs took about 41 and 95 seconds including source loading; another machine may differ. Seeds, normalization, pattern selection, block/FFT sizes, short-text omission and floating tie choices remain those of the source. No additional texts or manuscript windows are selected.

Compare the new outputs with the bundled expectations:

```text
python experiments/records/dukotah-held-corpus-skeleton-replay/compare_replay.py --t0 c01-t0-output/positive_control_T0.json --target c01-target-output/scan_results.json
```

The comparison checks every field, including per-text scores and chosen text/offsets. Floating values have absolute tolerance 0.001; integers, strings, lists and object fields must match exactly. A different floating tie choice is reported as a text/offset mismatch even when rounded scores agree. Retain the new outputs, versions and error instead of editing expectations or treating a mismatch as a cipher result.

Expected T0 plants are KJV at word offset 134137 and Emerson at 57592: each has exact count 2,506 and interval count 2,928. Expected real T1 maxima are exact **593/2,928**, slack-one **1,445/2,928**, interval **664/2,928**, and prefix interval counts **109/400** and **47/120**. The saved JSON supplies all shuffled and per-text expectations. Matching these outputs reproduces the bounded available-input scan; it does not reproduce the historical 224-text corpus or establish plaintext, language exclusion or a calibrated global probability.

## Quick saved-evidence audit

This separate command needs only the Python standard library. It checks bundled hashes, saved receipt consistency, summary arithmetic and the figure; **it does not run T0 or T1**:

```text
python experiments/records/dukotah-held-corpus-skeleton-replay/check.py --check
```

The older instructions and scripts under `reproduction/` are retained unchanged as frozen execution provenance. This document gives the current bundle-root commands.
