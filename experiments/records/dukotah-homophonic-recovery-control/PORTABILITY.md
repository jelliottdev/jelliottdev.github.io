# Reproduce the homophonic controls

Run these commands from the extracted bundle root, with its directories intact. The replay creates a fresh working directory and checks the saved results without overwriting them. It scores synthetic controls only, not manuscript targets.

## Dependencies and inputs

The recorded environment is Python 3.12.10 with NumPy 2.5.4. Install dependencies separately in your chosen environment; the scripts do not install packages. Local-Git input mode also requires Git and a local Dukotah/cicada3301 repository containing revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`.

Four external text files are required. They are not in this bundle. All four must match the exact byte counts and SHA-256 hashes below; paths are relative to the source repository. The first three supply the model and plants. The Old English file is checked as a frozen receipt member but no Old English model or control is run.

| Path | Bytes | SHA-256 | Runtime role |
| --- | --- | --- | --- |
| `liber-primus/data/keys/solved_plaintext.txt` | 17388 | `821cb3c89872bc33114055c9cdf81c7b38b33d3ac5711eaf753eeebaeefc6473` | English-labelled model/plant substrate; includes puzzle artifacts and notes |
| `liber-primus/data/keys/words_expanded.txt` | 4719 | `9b924d9d37f9b4ef5a49e2fc7f008c9ee48edbb77df9ea0edcd9a6faaa76269f` | Same substrate; word/key list |
| `liber-primus/data/keys/thematic.txt` | 378 | `f9db06ae01ed8437b98eeedaafe002fabab1665752b3be55c2ce5e25ba205d7f` | Same substrate; thematic words |
| `liber-primus/data/keys/runepoem_oe.txt` | 3382 | `e418d496af6ebf34281c60d98ab487a969b766101046bde40631007ed46c095c` | Hash-checked frozen receipt member; no OE model or control was run |

These are explicitly selected main-tree puzzle and key texts. They are not independent clean English prose or verified historical inputs from the recovered program’s missing data tree. The bundled `external-input-contract.json` and `source-receipt.json` retain the input provenance.

## Replay from a local source repository

Replace the quoted source path with your local repository. The replay reads pinned Git blobs, avoiding checkout line-ending differences:

```text
python experiments/records/dukotah-homophonic-recovery-control/replay_controls.py --from-git "/path/to/source-checkout" --workdir d03-replay
python experiments/records/dukotah-homophonic-recovery-control/plot_controls.py --check
```

Choose a new work directory; `d03-replay` must not already exist, and its parent must exist. A local-Git replay from a fresh bundle extraction passed. The producer took about 40 seconds on the recorded machine; total runtime also includes independent checks.

## Replay from prepared files

If you have an exact local source tree rather than its Git history, prepare the four files first. The utility validates all four before creating the new `d03-inputs` directory:

```text
python experiments/records/dukotah-homophonic-recovery-control/prepare_external_inputs.py --from-directory "/path/to/exact-source-tree" --out d03-inputs
python experiments/records/dukotah-homophonic-recovery-control/replay_controls.py --inputs d03-inputs --workdir d03-replay
python experiments/records/dukotah-homophonic-recovery-control/plot_controls.py --check
```

You can also prepare inputs with the same utility’s `--from-git "/path/to/source-checkout"` option instead of `--from-directory`. Keep the `liber-primus/data/keys/` layout under `d03-inputs`. Preparation and replay refuse existing output directories.

## Expected result and checks

Expect **0 of 3 completely recovered class streams**, and all three cases below both source detection gates. Partial class alignment is not complete recovery. These failed controls do not exclude homophonic substitution in Liber Primus.

The adapter stages the unchanged frozen producer, source functions and verified external files in an isolated directory, runs the controls, then invokes the independent checker. It compares all six saved output files’ deterministic JSON values exactly: scores, seeds, maps, arrays, null witnesses, types and decisions. Only benchmark samples, projected/total durations and `fit.seconds` are omitted from the comparison. The independent checker’s raw-results hash is checked against the new timing-bearing report. Expected files must remain unchanged. Success ends with `PASS: all deterministic control outputs and independent checks match; expected bytes unchanged.`

The checker independently reconstructs plants and scoring models, rescores retained maps and witnesses, and checks 1,500 held-out shuffle scores and all 24 equal-budget shuffled-fit witnesses. The 72 source unequal-budget null-fit witnesses and three single-shuffle maps were not retained; their aggregate moments remain producer summaries. The separate plot check verifies the saved chart against the recorded control values and result hash.

## Optional explicit download

If you choose to fetch the external inputs, use:

```text
python experiments/records/dukotah-homophonic-recovery-control/prepare_external_inputs.py --download --out d03-inputs
```

Then use the prepared-input replay commands above. This optional network mode has **not been exercised**. It uses only fixed raw GitHub paths at the pinned revision, with a 30-second timeout and exact per-file size/hash validation. No download occurs without this explicit option, and no packages are installed.

## Source and license

Recovered analysis code and documentation are by Dukotah, copyright 2026, at the pinned revision above. The bundled `source/LICENSE` gives MIT terms for original work and explicitly excludes puzzle artifacts and third-party/community transcriptions. It does not grant blanket rights to redistribute the external training texts. The exact source license is available at <https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/LICENSE>.
