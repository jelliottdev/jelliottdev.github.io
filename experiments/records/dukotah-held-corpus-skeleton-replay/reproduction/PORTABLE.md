# C-01 portable adapter — private publication proposal

This code/receipt bundle contains no corpus texts or derived length arrays. It preserves the original source modules and frozen scientific plans and results. The adapter changes only input/output paths. The source loader still normalizes raw text; all 94 raw and normalized hashes, exact loader names/order and manuscript arrays must agree before a scan can run.

Use Python 3.12 with `numpy==2.5.4` (the recorded environment). The `source/` directory contains exact modules from Dukotah/cicada3301 commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1` and its original MIT license. That code license does not settle individual corpus redistribution rights.

## External input setup

Use an existing local Git clone containing that commit. This adapter makes no clone, checkout or repository mutation. Git reads disable lazy fetching and credential prompts; missing local objects fail. Setup extracts only the 93 manifest-selected tracked texts and manuscript from the exact Git objects. KJV must be supplied separately, matching the frozen 4,436,268-byte SHA-256 pin in `inputs-frozen.json`.

```text
python portable.py setup --git /path/to/cicada3301 --destination /new/external-inputs --kjv-file /path/to/exact/kjv.txt
python portable.py verify --inputs /new/external-inputs
```

Alternatively, an explicit `--download-kjv` replaces `--kjv-file` and requests only the previously recorded public URL `https://www.gutenberg.org/files/10/10-0.txt`. It has a size limit and must match the exact hash; changed bytes or redirects fail. Downloading is optional and was not performed during adapter validation. A matching local artifact is already available in the earlier record as `experiments/records/dukotah-offset-model-integrity/source-kjv.txt`.

An existing external source tree can be used directly with `verify` if its selected raw bytes and loader membership agree. Extra eligible files, changed editions, wrong hashes or missing files are rejected. Existing setup/run destinations are never overwritten. Temporary setup is committed to the destination only after complete validation.

## Reproduction and parity

The explicit `run` command runs the unchanged source main function. It preserves the source's 2,928-word minimum-text gate for every pattern, the exact 21-pattern T1 selection, default block/FFT sizes, random seeds, floating scores and tie behavior. These commands perform scans; verification/importing alone does not.

```text
python portable.py run --inputs /new/external-inputs --stage t0 --output /new/t0-output
python portable.py run --inputs /new/external-inputs --stage target --output /new/target-output
```

The adapter validation uses local Git setup, compares every normalized array with the original source loader, and compares synthetic scanner outputs and blocked maxima at all three window lengths. It does not rerun the manuscript target:

```text
python test_portable.py --git /path/to/cicada3301 --kjv /path/to/exact/kjv.txt --receipt /new/portable-tests.json
python check_receipt.py
```

The older `replay.py` and related scripts are frozen provenance for the original private run and retain its repository-layout assumptions. `portable.py` is the external-input interface. `check_receipt.py` checks the immutable original receipts; the separate portable-stage and portable-test receipts document this adapter. No downloaded or staged corpus is included in the proposed publication bundle, and temporary local parity inputs are removed after testing.

## Publication file proposal

Publish only this allowlisted bundle after review: adapter and tests, immutable original plans/manifests/results/audits, original code plus MIT license, dependency pin and these instructions. Keep corpus inputs external. A future derived-array bundle remains a separate proposal; no arrays are included here. The original source normalization and limited historical coverage remain explicit; successful adapter parity does not turn this into the historical 224-text replay or a plaintext/language exclusion.
