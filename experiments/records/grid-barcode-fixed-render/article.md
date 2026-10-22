# LP2-49–51: does the fixed bit grid decode as a barcode?

**No valid QR Code or Data Matrix payload was found in the declared bit rendering.** The decoder returned zero valid payloads from 64 fixed-grid scans. It did decode both generated positive controls, so the null result is not simply a nonworking decoder. This result applies to the rendering and transformations below; it does not settle every way to rearrange the grid.

The [LP2-49–51 grid](#/wiki/alphanumeric-grids) contains 256 two-character entries. A [reported exploration](#/wiki/reported-attempts) converted them to binary and looked for QR-like or Data Matrix-like images. Its referenced result pictures and complete final plotting parameters were not preserved in the supplied text. We therefore test a **new, fully specified version** of that idea, rather than claiming an exact replay of every historical image.

## What went into the decoder

The pinned [grid-bit audit](exports/grid-binary-audit.json) reads each entry under the stated base-60 alphabet as one byte, then writes that byte as exactly eight bits, most significant first. Eight entries make a 64-bit manuscript row. We tested the complete 32-row grid and the original page groups separately: 10 rows from [LP2-49](#/reader/lp2-49), 13 from [LP2-50](#/reader/lp2-50), and 9 from [LP2-51](#/reader/lp2-51). The conditional base-60 and byte assumptions are explained in the grid guide; they are not an established cipher solution.

![Four fixed-width bit canvases, each with zero valid barcode decodes after 16 declared transformations.](experiments/records/grid-barcode-fixed-render/bit-canvases.svg)

For each canvas we tried four right-angle rotations, each with and without a horizontal reflection, in both color polarities: **16 scans per canvas, 64 total**. Every bit was an 8×8-pixel square with a four-module white border. We allowed no crop, row reflow, page permutation, added finder pattern, or missing bit. The scan used `zxing-cpp` 3.1.1 and accepted only a valid, nonempty QR Code or Data Matrix decode.

Two synthetic barcodes—one QR Code and one Data Matrix—decoded to their exact known strings with the same software and scan settings. Eight fixed-seed bit shuffles per canvas retained each canvas's dimensions and number of black bits; their 512 scans also yielded no valid payload. Those shuffles illustrate the background behavior of this detector, **not** the probability that the manuscript encodes a barcode. The [JSON report](experiments/records/grid-barcode-fixed-render/results.json) lists all 64 original transformations, image hashes, control settings, and outcomes.

## Reproduce and interpret

From the repository root, install the pinned Python dependency, then run:

```text
python -m pip install zxing-cpp==3.1.1 numpy
python experiments/records/grid-barcode-fixed-render/run.py --check
python experiments/records/grid-barcode-fixed-render/check.py
python experiments/records/grid-barcode-fixed-render/plot.py --check
```

The main script pins the input and plan hashes and rescans every case. The checker independently converts the [grid CSV](exports/alphanumeric-grids.csv) back to 2,048 bits, verifies manuscript row boundaries, and checks the saved census and controls. The figure script rebuilds the four pictured canvases from the same pinned bits.

This is a **negative result for four fixed canvases under 16 planar transformations each**. It does not test other disputed glyph readings, bit order, alternate widths, subwindows, padding, decoder settings, or other barcode types. Any broader image search should declare those choices and count every image examined before treating one apparent pattern as evidence.
