# Do the byte-grid values encode doublet spacing?

**No direct rank alignment was found under seven specified byte readings.** The strongest absolute correlation is **0.119**, below the published 0.5 gate. This checks one way the [LP2-49–51 numerical grid](#/wiki/alphanumeric-grids) might encode positions of repeated adjacent runes elsewhere in LP2; it does not assess every possible use of the grid.

![Seven payload readings compared with the gap sequence. All bars fall below the declared 0.5 gate.](experiments/records/payload-doublet-gaps/gap-correlation.svg)

An equal-rune pair is called a *doublet*. There are 86 such pairs within the archived LP2-00–55 page texts. Put their starting rune positions in page order, then subtract each from the next: that makes **85 gaps**. The first few are `85, 249, 197, 129`. We compared this sequence with numbers read from the published 256-byte grid file, beginning at byte zero each time.

| Byte reading | Values used | Correlation with 85 gaps |
| --- | ---: | ---: |
| One unsigned byte per number | 85 | +0.043 |
| Two-byte integers, little endian | 85 | −0.018 |
| Two-byte integers, big endian | 85 | −0.026 |
| LEB128, forward / reversed bytes | 85 each | −0.027 / +0.004 |
| MSB-first base-128, forward / reversed bytes | 85 each | −0.040 / −0.004 |

The source's later varint test also prepended the one-based location of the first doublet, **122**, making an 86-value target. The largest absolute correlation across both targets is **0.119**: forward LEB128 against that 86-value sequence. [The full result table](experiments/records/payload-doublet-gaps/results.json) retains all 14 comparisons and the number of values each decoding produced.

## How the comparison was checked

The statistic is Spearman's rank correlation: it asks whether large payload numbers tend to line up with large doublet gaps, without requiring their magnitudes to match. The test fixes the reading direction and starts at the first byte and first gap. It does **not** shift the payload until a favorable match appears. As an alignment check, we circularly shifted the 85-gap target through its other 84 positions, repeating the largest-of-seven comparison each time. **83 of 84** shifted alignments matched or exceeded the unshifted maximum. Those shifts are dependent descriptive controls, not a calibrated cipher null or a p-value.

Encoding all 85 actual gaps into either varint format and decoding them again recovers every gap exactly. A separate checker recomputes all 14 correlations with a different midrank algorithm. This establishes that the tested encoders and rank calculations work; it does not prove the grid cannot hide a transformed gap list.

The [earlier published fixed-width check](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/zeroFP/zerofp_tests.py) used unsigned 8- and 16-bit values. A [later extension](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round28/L5/l5_payload_micro.py) tested the two variable-length readings and both byte directions. This replay uses the pinned source byte file and Liberpedia's separately archived [doublet coordinates](#/experiments/doublet-placement). No inference is made about alternate grid transcriptions, arbitrary offsets, other encodings or a decoder that first transforms the bytes.

## Reproduce

Extract this experiment and the reference-data bundle together, then run:

```sh
python experiments/records/payload-doublet-gaps/run.py --check
python experiments/records/payload-doublet-gaps/check.py
```

Both scripts use only the Python standard library.
