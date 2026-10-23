# Do the lines carry another message?

This [published test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/C3/l3) measures the line layout in the 56 unsolved LP2 page images. It asks whether line height, margins, spacing, or rune counts form a second data channel. We ran its two programs on the **exact 56 JPEGs** used by the source and reproduced their saved results: every count and verdict matches; eleven floating-point values differ by less than 10⁻¹².

## What did the search find?

The source measured **616 image rows**. Five of eleven measured features split into two groups under its mixture-model rule. That is a property of the layout, **not a decoded message**. Its eight specified bit-decoding searches found no qualifying English four-gram pattern.

One correlation also crossed the source's multiple-test threshold: lines with more runes tended to have lower mean rune indices (*ρ* = −0.257). A width-adjusted calculation fell to *ρ* = −0.018. This suggests a typographic explanation, but the source pairs image rows and canonical text lines by position even though there are **616 versus 604**; that alignment needs checking before interpreting the cross-domain relationship. The rune-count/rune-index correlation itself uses the canonical lines.

## Did the decoder pass its own controls?

![The strongest planted line-fill signal recovered 85.9% of bits, below the required 95%; a separate ASCII plant matched 29 of 77 intended characters despite a source PASS label.](experiments/records/dukotah-line-geometry-channel-replay/control-gates.svg)

The source required **95% recovery** of a planted 64-bit message to establish sensitivity. Its strongest line-fill plant recovered **55 of 64 bits (85.9%)**; none of seven tested strengths passed. In a separate noise-free ASCII plant, the source marked a four-gram score as “PASS.” We reconstructed the actual decoded text: only **29 of 77 characters** match the planted text. A favorable score did not mean the message was recovered.

The eight negative bit scans therefore describe **this decoder on these channels**. They cannot exclude a line-based message that this procedure lacks the power to recover. Nor do the measured layout groups by themselves establish such a message.

## Reproduce

The [frozen replay plan](experiments/records/dukotah-line-geometry-channel-replay/source-replay-plan.json) pins source files, rules, and image hashes. Extract the [original images](downloads/original-images.zip) into `images/`, or use a complete Liberpedia checkout. The experiment ZIP includes the pinned MIT-licensed source subset. From the repository root, with Python, NumPy, SciPy, and Pillow:

```text
python experiments/records/dukotah-line-geometry-channel-replay/run.py --check
python experiments/records/dukotah-line-geometry-channel-replay/check.py --check
python experiments/records/dukotah-line-geometry-channel-replay/plot.py --check
```

The [source geometry rows](experiments/records/dukotah-line-geometry-channel-replay/source-linegeom.json), [source tests](experiments/records/dukotah-line-geometry-channel-replay/source-linetests.json), [summary](experiments/records/dukotah-line-geometry-channel-replay/results.json), and [independent control recount](experiments/records/dukotah-line-geometry-channel-replay/independent-controls.json) are included. The plan was frozen before our replay, **after** the source findings were known; this is a source check, not an independent preregistration.
