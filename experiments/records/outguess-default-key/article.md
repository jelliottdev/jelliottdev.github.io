# Original JPEGs: default-key OutGuess retrieval

## Why run this?

Some known Liber Primus images contain messages recovered with OutGuess. A newcomer may reasonably try the same operation on the other images. This experiment records what that particular retrieval does, including failures and unverified output, instead of assuming that every byte stream is a message or every failure means an empty image.

## Plan fixed before execution

The runner and plan were committed as `8bca8ba` before the first run. The scope is all 75 archived manuscript JPEGs, plus the 2014 opening image and the compasses cover. Every original-image SHA-256 is fixed in the plan. Thumbnails, screenshots and recompressed images are excluded.

Each image receives exactly one invocation of OutGuess with retrieval mode and the literal key `Default key`. The timeout is 20 seconds per invocation. Ten expected payload hashes serve as positive controls. All output files, exit codes and stderr diagnostics are retained, including empty output files and abnormal exits. A second complete run checks reproducibility; it is not counted as 77 additional independent discoveries.

## Result

| Observed category | Images | What it establishes |
| --- | --- | --- |
| Known payload hash reproduced | 10 | Exact agreement with the archived extraction control |
| Nonempty output, exit code 0, no control | 21 | Unverified candidate bytes only |
| Retrieval rejected, exit code 1 | 5 | This retrieval did not succeed |
| Abnormal exit code 3221225620 | 41 | An unresolved failure of this tool/build on these inputs |
| Timeout | 0 | No invocation exceeded the declared time limit |

All 77 invocations were attempted. Ten controls matched. **The other 67 images are not established as free of hidden data.** The 21 candidate outputs are not authenticated messages, and the 41 abnormal exits prevent treating this as a clean image-wide negative result.

The repeated output length 58,152 occurs in 19 candidate records. It is a reported extraction length, not a discovered structure in the manuscript. The 21 candidate byte streams have distinct hashes. None contains the ASCII marker `-----BEGIN PGP SIGNED MESSAGE-----`; that limited observation neither validates nor rules out a different encoding or payload type. No signature verification or interpretation of candidate contents was performed in this experiment.

## How to reproduce

Use Python 3.12.10 and a locally available OutGuess executable. See the [OutGuess guide](#/wiki/outguess) for original-file selection and the known-payload controls.

```
python experiments/records/outguess-default-key/run.py --outguess outguess --output my-outguess-run
python experiments/records/outguess-default-key/check.py
```

The first command creates a new directory, refuses to reuse an existing one, and records your executable's SHA-256. Replace `outguess` with its full executable path if necessary. The second command audits the saved experiment: every image hash, output hash, expected control and record count. It does not run OutGuess.

To repeat the exact saved run with the same executable:

```
python experiments/records/outguess-default-key/run.py --outguess outguess --check
```

This checks the tool hash, all statuses, diagnostics and every saved payload byte. Paths to temporary files are normalized in diagnostics; diagnostic content is otherwise retained. A different binary or platform may legitimately produce different diagnostics or error behavior. Run it into a new directory and compare it as a build variant rather than replacing this baseline.

## Tool and build limitation

The recorded binary was a local Windows port of upstream commit `24810e14327c2bbeedeaadd3e24491f2a4425c02`, built using MinGW-W64 GCC 16.1.0. Its SHA-256 is `b342b8b85d678d3b2ed26efab70fba2b3956725670be7149b89646868f0ebade`.

The existing build record describes use of the upstream allocation/read fallback instead of mmap, a compatibility byte-order helper, and binary-mode input on Windows. Matching the ten controls checks those particular extraction paths; it does not establish correct behavior on all other images. The 41 abnormal exits remain a substantial limitation. The executable is not included in the wiki downloads. A reader with a different build should preserve their new report as a comparison, not expect its executable hash to match.

## Retest and review

Codex ran the entire 77-image sweep twice on 20 October 2026. All return codes, normalized diagnostics and output bytes matched exactly. A separate saved-file audit checked all image and output hashes and the ten control comparisons. The original plan, key, timeout and image list did not change after the first run. The visual map was generated from the saved report; it does not run another extraction. Human review remains pending.

## What to test next

The most informative next variant is another documented OutGuess build on exactly the same files and key, focusing on whether the 41 abnormal exits persist. A new key is a different variable and should not be changed simultaneously if the purpose is to isolate build behavior. Other steganographic methods require their own clearly scoped experiment.

## Per-image results

The table below lists every invocation. Full diagnostics and exact hashes are in [the machine-readable report](experiments/records/outguess-default-key/results/report.json). Raw output downloads are listed under the record's output checksums; unverified bytes must not be described as decoded messages.

| Image | Category | Exit code | Output bytes |
| --- | --- | --- | --- |
| lp1-00 | Known control matched | 0 | 2899 |
| lp1-01 | Known control matched | 0 | 2899 |
| lp1-02 | Known control matched | 0 | 2899 |
| lp1-03 | Known control matched | 0 | 31809 |
| lp1-04 | Unverified output | 0 | 7524 |
| lp1-05 | Rejected | 1 | 0 |
| lp1-06 | Unverified output | 0 | 58152 |
| lp1-07 | Unverified output | 0 | 58152 |
| lp1-08 | Unverified output | 0 | 140 |
| lp1-09 | Unverified output | 0 | 58152 |
| lp1-10 | Known control matched | 0 | 1234 |
| lp1-11 | Known control matched | 0 | 1234 |
| lp1-12 | Known control matched | 0 | 1234 |
| lp1-13 | Known control matched | 0 | 1234 |
| lp1-14 | Abnormal tool exit | 3221225620 | 0 |
| lp1-15 | Rejected | 1 | 0 |
| lp1-16 | Abnormal tool exit | 3221225620 | 0 |
| lp2-00 | Unverified output | 0 | 58152 |
| lp2-01 | Abnormal tool exit | 3221225620 | 0 |
| lp2-02 | Abnormal tool exit | 3221225620 | 0 |
| lp2-03 | Abnormal tool exit | 3221225620 | 0 |
| lp2-04 | Unverified output | 0 | 58152 |
| lp2-05 | Abnormal tool exit | 3221225620 | 0 |
| lp2-06 | Abnormal tool exit | 3221225620 | 0 |
| lp2-07 | Abnormal tool exit | 3221225620 | 0 |
| lp2-08 | Abnormal tool exit | 3221225620 | 0 |
| lp2-09 | Abnormal tool exit | 3221225620 | 0 |
| lp2-10 | Abnormal tool exit | 3221225620 | 0 |
| lp2-11 | Abnormal tool exit | 3221225620 | 0 |
| lp2-12 | Abnormal tool exit | 3221225620 | 0 |
| lp2-13 | Abnormal tool exit | 3221225620 | 0 |
| lp2-14 | Abnormal tool exit | 3221225620 | 0 |
| lp2-15 | Abnormal tool exit | 3221225620 | 0 |
| lp2-16 | Abnormal tool exit | 3221225620 | 0 |
| lp2-17 | Abnormal tool exit | 3221225620 | 0 |
| lp2-18 | Abnormal tool exit | 3221225620 | 0 |
| lp2-19 | Abnormal tool exit | 3221225620 | 0 |
| lp2-20 | Abnormal tool exit | 3221225620 | 0 |
| lp2-21 | Abnormal tool exit | 3221225620 | 0 |
| lp2-22 | Abnormal tool exit | 3221225620 | 0 |
| lp2-23 | Abnormal tool exit | 3221225620 | 0 |
| lp2-24 | Abnormal tool exit | 3221225620 | 0 |
| lp2-25 | Abnormal tool exit | 3221225620 | 0 |
| lp2-26 | Unverified output | 0 | 58152 |
| lp2-27 | Abnormal tool exit | 3221225620 | 0 |
| lp2-28 | Abnormal tool exit | 3221225620 | 0 |
| lp2-29 | Abnormal tool exit | 3221225620 | 0 |
| lp2-30 | Abnormal tool exit | 3221225620 | 0 |
| lp2-31 | Abnormal tool exit | 3221225620 | 0 |
| lp2-32 | Rejected | 1 | 0 |
| lp2-33 | Abnormal tool exit | 3221225620 | 0 |
| lp2-34 | Abnormal tool exit | 3221225620 | 0 |
| lp2-35 | Abnormal tool exit | 3221225620 | 0 |
| lp2-36 | Abnormal tool exit | 3221225620 | 0 |
| lp2-37 | Abnormal tool exit | 3221225620 | 0 |
| lp2-38 | Abnormal tool exit | 3221225620 | 0 |
| lp2-39 | Abnormal tool exit | 3221225620 | 0 |
| lp2-40 | Unverified output | 0 | 58152 |
| lp2-41 | Unverified output | 0 | 58152 |
| lp2-42 | Unverified output | 0 | 58152 |
| lp2-43 | Unverified output | 0 | 58152 |
| lp2-44 | Unverified output | 0 | 58152 |
| lp2-45 | Unverified output | 0 | 58152 |
| lp2-46 | Unverified output | 0 | 58152 |
| lp2-47 | Unverified output | 0 | 58152 |
| lp2-48 | Unverified output | 0 | 58152 |
| lp2-49 | Abnormal tool exit | 3221225620 | 0 |
| lp2-50 | Abnormal tool exit | 3221225620 | 0 |
| lp2-51 | Unverified output | 0 | 58152 |
| lp2-52 | Unverified output | 0 | 58152 |
| lp2-53 | Unverified output | 0 | 58152 |
| lp2-54 | Unverified output | 0 | 58152 |
| lp2-55 | Abnormal tool exit | 3221225620 | 0 |
| lp2-56 | Rejected | 1 | 0 |
| lp2-57 | Rejected | 1 | 0 |
| opening-2014 | Known control matched | 0 | 1150 |
| 1033 | Known control matched | 0 | 1498 |
