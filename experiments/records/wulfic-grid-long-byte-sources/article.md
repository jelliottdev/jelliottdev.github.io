# Can archived byte streams unlock the number grid?

The [number grid on LP2-49–51](#/wiki/alphanumeric-grids) contains 256 printed cells that can be read as bytes. Wulfic's Stage Y uses six specified byte streams as repeating keys, starting at **every possible position** in each stream. It checks four ways to traverse the grid and four byte operations.

**Result:** none of the **96 source × route × operation cells** contains a phase that meets the source's pass rule. The lowest decoded block has **139 distinct byte values**; the declared cutoff is **120**. All **24 planted positives** pass, and all **18 random-grid negatives** stay above the cutoff. The original two result tables were reproduced byte-for-byte, and our checker independently recomputed all **2,865,136 phase trials** from the site's grid transcription.

![The lowest distinct-byte count from each of six source files remains above the declared cutoff](experiments/records/wulfic-grid-long-byte-sources/comparison.svg)

Here “distinct” means how many different byte values appear in a complete 256-byte output. A block restricted to ordinary text or a small alphabet may have few; a nearly uniform block generally has more. This is a **screen for low byte diversity**, not a text decoder. An intelligible answer with more than 120 different byte values would not pass this screen.

## What was tested

The six inputs are three archive files named `page_17.bin`, `page_21.bin`, `page_43.bin`, the archived wisdom hint, 991 bytes parsed from the `page_00` hex text, and 256 bytes parsed from the second-onion hex string. The file numbers are **source archive names**, not a claim that they belong to manuscript pages LP2-17, LP2-21 or LP2-43. Their exact bytes and hashes are bundled with this record.

For each source, the key starts at every cyclic phase. The grid is read in printed row order, its reverse, column order, or its reverse. Each route is combined with XOR, grid minus key, grid plus key, or key minus grid modulo 256. This gives **16 cells per source**, each covering every phase. The [full 96-cell table](experiments/records/wulfic-grid-long-byte-sources/source-stage_y_results.tsv) preserves the lowest count, its source phase, and the exact-source verdict. The best cell uses `page_43.bin`, printed row order and XOR at phase 43,059; its count is 139.

The source's rule treats a cell as excluded when none of its phases has at most 120 distinct values. Its controls are part of that claim: every planted text, rune, hex and base64 case must pass at its planted location; random grids must produce no passes, with a mean distinct count within 0.5 of 162. The [42-row control table](experiments/records/wulfic-grid-long-byte-sources/source-stage_y_controls.tsv) records those checks. The source run reports a valid gate. This does **not** rule out a message that remains high-diversity under the chosen operation.

## Reproduce

The [plan](experiments/records/wulfic-grid-long-byte-sources/plan.json) fixes the six inputs, four routes, operations, all-phase rule and threshold. The experiment download includes all six exact byte inputs. The checker reads Liberpedia's 256 grid tokens, parses them independently as base-60 bytes, calculates every phase, and checks each published minimum, phase, mean, printable fraction, probability and verdict. It also tests 24 separately planted known-byte controls. Run from the repository root with Python and NumPy:

```text
python experiments/records/wulfic-grid-long-byte-sources/run.py --check
python experiments/records/wulfic-grid-long-byte-sources/plot.py --check
```

We also reran the [pinned Stage Y program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_y.py) at commit `bf89d3d`. With that external checkout, the optional wrapper recomputes the source's own controls and results in a temporary directory and verifies them against its committed tables:

```text
python experiments/records/wulfic-grid-long-byte-sources/replay_source.py PATH_TO_WULFIC_CLONE
```

This only covers the six byte streams, the printed grid, these four routes and operations, and the source's diversity cutoff. It does not test other keys, another grid construction, inserted or skipped bytes, decompression after a keyed transform, or a plaintext whose bytes remain diverse.
