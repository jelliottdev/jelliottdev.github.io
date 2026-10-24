# Reproduce the autokey-with-skips grid

Install Python 3.12, NumPy 2.5.4 and Numba 0.67.0 separately. Nothing here installs packages or fetches remote data. Extract the bundle with its repository-relative folders intact and run from the extracted root.

Check declared bytes, all 9,900 saved source and normalized winning-output scores, strict gates and control counts without the external manuscript:

```sh
python experiments/records/autokey-skip-family/check.py
```

Prepare the exact external transcription from an existing local Dukotah/cicada3301 Git checkout, then replay everything into temporary files:

```sh
python experiments/records/autokey-skip-family/prepare_input.py --git-source /local/cicada3301 --output autokey-manuscript.txt
python experiments/records/autokey-skip-family/replay.py --transcription autokey-manuscript.txt
```

The preparation script reads revision f08b20b632d91209ddbaa747e8e2f23df0c78ba1 and validates SHA-256. An already prepared transcription with the same hash is also accepted. The full replay repeats all 360 known-reading cases and the complete target grid, compares every deterministic JSON field and numerical/output array, and invokes the independent target audit. Elapsed timings are excluded. Existing expected evidence is untouched; the source target runner has a 1,800-second execution cap.

Expected target result: zero source-gate crossings in 9,900 full-page decodes, and zero crossings in the separate retained-terminal normalized-score diagnostic. The original complete grid took about 100 seconds on the recorded machine; other computers may differ.

The controls must retain their failures: only 113 generated readings are admissible under the corresponding decoder, and all 113 recover; the other 247 depend on future-key behavior the paired encoder and decoder handle differently. Scores can also pass for wrong text. These results measure the specified source algorithms, not a validated exclusion of autokey ciphers.

Exact source/model/parser bytes, known readings, frozen plans and independent receipts are included. The raw manuscript transcription remains external. Source code and quadgram counts are supplied under the pinned repository's MIT license. The selective loader executes only required definitions, avoiding unrelated corpus setup; it does not change the source encoder, decoder or score rules.
