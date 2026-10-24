# Reproduce the fixed prediction and compression test

Use Python 3.12, NumPy 2.5.4 and Numba 0.67.0, installed separately. LZMA is part of Python’s standard library. The canonical run used Python 3.12.10 on Windows; compressed byte counts can depend on the Python/liblzma build. Differences are failures to investigate, not permission to replace expected results. These scripts install nothing and make no network requests.

Commands start at the extracted bundle root. The source transcription is external: neither its text, compressed text nor rune-index sequence is redistributed in this record. Obtain the exact file from an explicit local checkout containing source revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`:

```sh
python experiments/records/heldout-rune-prediction/prepare_input.py --git /path/to/cicada3301 --destination /path/to/new-exact-transcription.txt
python experiments/records/heldout-rune-prediction/check.py
python experiments/records/heldout-rune-prediction/replay.py --transcription /path/to/new-exact-transcription.txt
```

The preparation command disables lazy Git fetching and authentication prompts, validates the byte hash, and refuses to overwrite an existing destination. Alternatively supply the exact file directly. Any edition or byte mismatch stops the replay.

The quick check needs no external transcription. It checks frozen file hashes, all saved reference rows, page/fold aggregation and the public summary against the full observed outputs. It does not reconstruct the manuscript.

For independent target reconstruction using the saved reference bank, without rerunning its 1,000 streams:

```sh
python experiments/records/heldout-rune-prediction/reproduction/independent/audit_public.py --record-root experiments/records/heldout-rune-prediction --transcription /path/to/new-exact-transcription.txt
```

Full replay stages the unchanged producer in a temporary directory and validates the external transcription there. It reruns the 199-reference/99-validation/18-plant synthetic study, all 1,000 final reference streams, and the fixed manuscript grid. It compares all deterministic fields and arrays, ignoring runtime durations only. Frozen timing metadata are restored only in that temporary copy because the original authorization binds those exact reference bytes. It then invokes the unchanged independent checker to reconstruct every target predictor/page loss, both LZMA views, all eight provenance metrics, the family rank and uniform gains. Original expected files remain untouched. Allow a few minutes including compilation and independent checking.

Expected output: no marginal 1% flags, family rank 36/1,001 (35 controls at least as strong), and no joint gate passage. Two KT orders have tiny positive gains over uniform; three are equivalent within the frozen tolerance. Packed LZMA flagged none of the 18 synthetic examples, including all twelve deliberately strong patterns, and was constant across all 1,000 reference streams. That limitation remains part of the result.

`reproduction/METHODS.md` explains the exact models and limitations; the frozen protocol, authorizations and receipts preserve their original bytes. Historical independent bank/control audit scripts are retained as provenance; replay and the standalone adapter invoke the unchanged `reproduction/independent/audit_target.py` checker in their temporary stage. The source code is MIT (Dukotah, 2026); the retained `reproduction/source/LICENSE` distinguishes third-party material. The new model choices are a bounded implementation of a public proposal, not a historical replay or a proof about OTPs.
