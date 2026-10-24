# Reproduce the supplied-payload source completion

Extract the ZIP with its folders intact. Run all commands from the extraction root, containing `experiments/` and `scripts/`. The same commands work from the repository root. Python 3.12 standard library is sufficient; no download, model or paid service is used.

```text
python scripts/verify_bundle.py EXPERIMENT-lp2-pad-payload-target-CONTENTS.json
python experiments/records/lp2-pad-payload-target/check.py --check
python experiments/records/lp2-pad-payload-target/run.py --output f01-fresh-output
```

The output directory must not exist. The last command actually runs the source original control, eight full-length plants, the 40 original primary rows, eight supplied-payload rows and one new 200-shuffle panel shared by two exact aliases. It then compares the fresh control/target results against the bundled expectations. The three selected old null receipts remain frozen source results; it does not rerun the historical old null panels. Typical time is tens of seconds; retain the actual timing from your machine.

The separately frozen exact-recovery control is expected to **fail**: seven plants recover 256/256 runes; reversed-key/+ recovers 253/256. The original source control is expected to pass its different 80% character-recovery gate. Continuing to the target is explicitly authorized by the immutable pre-target diagnostic amendment. A successful replay reproduces this failure and the resulting inconclusive diagnostic; it does not certify the key model or establish plaintext.

Fresh files are `f01-fresh-output/control-results.json` and `f01-fresh-output/target-results.json`. To repeat only the comparison:

```text
python experiments/records/lp2-pad-payload-target/run.py --compare f01-fresh-output
```

Comparison checks every key, list, label, rune output, score, pointer, null score and selection. Only elapsed/decode timing fields, the benchmark derived from those timings and the fresh target-plan hash are excluded. Floats use absolute tolerance 1e-10. A changed score, output or tie choice fails; retain the error rather than changing expectations.

`run.py` changes file paths only. It verifies staged scientific bytes against `inputs-frozen.json`, then calls the unchanged frozen runner/source functions. The fresh target plan records the fresh control receipt hash while retaining the same failed-gate diagnostic authorization. External paths in `inputs-frozen.json.files` are archival provenance for the original freeze, not dependencies fetched during replay. The source tree and its MIT license are bundled; no caches are included.

Source: Dukotah/cicada3301 commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. Supplied payload SHA-256: `4c8dc85531d256793a6d0d318b8845869b4983e672077b094ed955bde92226d5` (256 bytes). It is committed `canon_256.bin`, staged at the source loader’s first candidate `payload.bin`; this does not recover or identify the unavailable historical payload.bin. LP2 key length is 12,956 runes. The original 63-byte AN END target is unchanged.
