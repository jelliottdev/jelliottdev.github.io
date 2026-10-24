# Reproduce the keyword-with-skips search

Install Python 3.12, NumPy 2.5.4 and Numba 0.67.0 separately. The commands install nothing and make no network requests. They work from an extracted experiment bundle, whose files retain their repository-relative paths.

Check the saved score grid, all phase selections, control counts and every declared file:

```sh
python experiments/records/keyword-skip-family/check.py
```

The raw manuscript transcription remains external. Prepare the exact pinned bytes from an existing local Dukotah/cicada3301 Git checkout, or supply an already prepared file with the documented SHA-256:

```sh
python experiments/records/keyword-skip-family/prepare_input.py --git-source /local/cicada3301 --output keyword-manuscript.txt
python experiments/records/keyword-skip-family/replay.py --transcription keyword-manuscript.txt
```

The full replay stages files in a temporary directory, repeats all synthetic controls and the complete 619,080-screen source grid, compares every deterministic result and score array, and invokes the independent target audit. Only elapsed timings are ignored. Existing evidence is never overwritten. The measured target runtime was about 81 seconds, plus synthetic controls and compilation; other computers may differ.

Expected results: 617 own-key tests pass the source score gates, 575 recover completely; three of four complete vocabulary searches recover the full known reading. No manuscript screen passes the first source gate, so there are no full-page target outputs. These are algorithm measurements, not a general cipher exclusion.

Source code and quadgram counts are pinned to revision f08b20b632d91209ddbaa747e8e2f23df0c78ba1 under the supplied MIT license. `reproduction/inputs-frozen.json` identifies exact inputs. The selective loader avoids unrelated corpus setup; source decoder, vocabulary, gates, tiling and parser bytes are unchanged. The accelerated beam was checked against ordered native terminal beams before target scoring.
