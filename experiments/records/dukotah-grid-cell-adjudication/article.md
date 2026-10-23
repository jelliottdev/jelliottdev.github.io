# Which bytes are printed in the base‑60 grid?

The LP2-49–51 table contains **256 two-character cells**. Some transcriptions agree on a token while a derived decimal column gives a different byte. The [source A‑04 investigation](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L5-payload) used the original page images to examine six such cells. We replayed its grid, calibration scorer and pixel matcher on JPEGs whose hashes match the source's archived-image manifest.

![Six cells cropped from the original pages. Each source pixel reading and base-60 value differs from the competing decimal-column value.](experiments/records/dukotah-grid-cell-adjudication/six-cells.svg)

All six image readings reproduce: **3I, 0I, 2l, 0l, 1O, 0W**. They convert to **198, 18, 167, 47, 84, 32**, matching the source's chosen token column rather than the competing decimal column. The separate source extension checked all eleven disputed cells and reported three changes to its pre-existing `canon_256.bin` at indices **45, 50 and 246**. That extension is included in the replay receipt; it was not part of the six-cell preregistered question.

## Why trust the readings, and how far?

The source first required **at least 38 of 40** saved blind calibration readings to match the known tokens. Its saved readings score **40/40** when rescored here. The automated nearest-exemplar control classifies **236/237** testable trailing glyphs correctly. Some decisive classes (`I`, `i`, `l`) have only one uncontested exemplar, so they cannot be leave-one-out tested. The source also saved three concordant visual readings of each of the six cells. Our code can reproduce the image grid and pixel results, but it cannot independently verify that those historical human reads were blind.

These are **printed-byte measurements**, not a way to decode the resulting 256-byte payload. The source's pixel-matching method and the competing transcription share the same finite image; agreement between them should not be counted as independent historical witnesses. This check does not resolve other copies, transformations or cryptographic interpretations of the payload.

## Reproduce

The [replay plan](experiments/records/dukotah-grid-cell-adjudication/replay-plan.json) pins source revision, six cell indices and the SHA-256 of all three images. Extract [original images](downloads/original-images.zip) into `images/` or use the full checkout. With Python, Pillow and NumPy, run from the repository root:

```text
python experiments/records/dukotah-grid-cell-adjudication/run.py --check
python experiments/records/dukotah-grid-cell-adjudication/plot.py
```

The first command runs five unmodified source programs in a temporary directory and [checks their saved outputs](experiments/records/dukotah-grid-cell-adjudication/check.py). The [source output](experiments/records/dukotah-grid-cell-adjudication/adjudication.json) and [replay output](experiments/records/dukotah-grid-cell-adjudication/replay-output/adjudication.json) are both retained. The plan was frozen before this replay, after the source result was available; it is **not** a new preregistration.
