# Does the printed grid contain a compressed stream?

The 256 cells on [LP2-49–51](#/wiki/alphanumeric-grids) can each be read as one base-60 byte. Wulfic's Stage X4 passes the **complete 256-byte grid** to five standard decompressors in four fixed reading orders. It also checks the same four streams for known file starts.

**Finding:** none of the **20 decoder calls** reaches the end of a compressed stream. None of the four streams matches the source's offset-zero file signatures. We reran the pinned X4 component and reproduced all **24 published rows** exactly; an independent checker rebuilt the grid from Liberpedia's tokens, repeated the five 100,000-block calibrations and checked every decoder result.

![Four complete grid routes under five decoders; none reaches the end of a compressed stream](experiments/records/wulfic-grid-compression-source-replay/decoder-screen.svg)

The four orders are printed rows, reversed rows, columns of the 32 × 8 grid, and reversed columns. The five decoders are **raw DEFLATE, zlib, gzip, bzip2 and LZMA**. No byte is skipped, reordered within a route, keyed, or prefixed with a header. The [complete X4 result table](experiments/records/wulfic-grid-compression-source-replay/source-stage_x4_rows.tsv) keeps each decoder error and verdict.

## Why the random-stream check matters

The source applied each decoder to **100,000 seeded random 256-byte blocks**. Raw DEFLATE reached end-of-stream **552** times; the other four decoders had **zero observed hits** in their respective samples. A raw DEFLATE end marker alone would therefore be weak evidence here. Zero observed calibration hits is a sample result, **not** proof that a format can never accept random bytes.

The source accepts `eof=True` from a single bounded decoder call, with at most **1 MiB of output**. It does **not** require every input byte to be consumed. Our separate synthetic controls confirm that all five implementations recognize a complete compressed message, reject a truncated one, and still report EOF when junk follows a complete stream. These controls were added **after** the source replay to check the implementation; they were not part of Stage X4's original power gate.

The result excludes only an end-of-stream under these five APIs on these four exact 256-byte readings. A stream beginning at another offset, a different rendering of contested grid cells, a keyed transform, a larger output stopped by the cap, or another compression format remains outside this test. This also differs from the [direct-byte screen](#/experiments/grid-direct-bytes), which checks text and file headers rather than running full decompressors.

## Reproduce

From the repository root, with Python and NumPy:

```text
python experiments/records/wulfic-grid-compression-source-replay/run.py --check
python experiments/records/wulfic-grid-compression-source-replay/plot.py --check
```

The [plan](experiments/records/wulfic-grid-compression-source-replay/plan.json) fixes the input export, decoder APIs, routes, output cap, random seed and verdict rule. The [independent report](experiments/records/wulfic-grid-compression-source-replay/results.json) separates the manuscript results from calibration and the later diagnostics.

With the [pinned Stage X program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_x.py) at commit `bf89d3d`, this command reruns **X4 only**, compares every row with the committed Stage X table, and writes no file into the external checkout:

```text
python experiments/records/wulfic-grid-compression-source-replay/replay_source.py PATH_TO_WULFIC_CLONE
```
