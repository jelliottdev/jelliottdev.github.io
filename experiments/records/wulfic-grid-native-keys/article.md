# Do native Cicada keys read the number grid?

The 256 printed cells on LP2-49–51 can be converted to bytes under the documented base-60 convention. Wulfic's Stage N tests whether several keys drawn from earlier Cicada material make those bytes resemble text, a file, or runes. **None of its 456 fixed settings reaches its own reading screen.** This is a bounded keyed-grid check, not a claim that the grid has no encoded message.

![Best byte-printability and GP29 likelihood compared with the original source thresholds](experiments/records/wulfic-grid-native-keys/comparison.svg)

## The two screens

The **byte screen** uses the printed 32 × 8 grid in row order or its full reversal. For each, it repeats one of 12 source keys and applies XOR, byte subtraction or byte addition. Those **72 outputs** are screened for at least 90% printable bytes or an offset-zero signature such as PNG, JPEG, gzip, ZIP, PDF or a length-consistent OpenPGP packet header. The best printable fraction is **42.6%**; no signature is reported. A printable result would only be a candidate, not a proven reading.

The **rune screen** takes either the 256 grid bytes modulo 29 or the 512 individual base-60 digits modulo 29. In each representation it tests forward and reversed order. It then scores three GP29 decoding directions under every constant shift, plus the source's prime, `DIVINITY` and `FIRFUMFERENFE` streams. These **384 settings** use the source's drift-tolerant solved-LP1 rune-frequency detector. The largest log-likelihood ratio is **4.63 nats**, below the source pass level of **+30**.

The [complete 456-row source result](experiments/records/wulfic-grid-native-keys/source-stage_n_results.tsv) retains each key, operation, direction, screen value and verdict. The byte screen uses a permissive printable threshold; the rune screen is a unigram detector. Neither tests whether a longer decoded phrase is meaningful or whether a key derived from different puzzle material works.

## What this does and does not establish

The original Stage N run did **not** include a planted detector-control gate. We regenerated its table exactly, then added separate, **post-replay** checks that its byte operations can recover synthetic printable text and that its rune likelihood can recognize a simple planted high-signal case. Those diagnostics catch broken implementations; they are not a preregistered LP2 power study and do not justify rejecting a whole cipher family.

The result is about the source's row-order grid, full reversal, named keys, operations, two rune encodings and two fixed thresholds. It does not cover other grid routes, uncertain glyph readings, offsets within a file, key starts and drift models beyond the source, decompression after decryption, or different languages. The [direct-byte experiment](#/experiments/grid-direct-bytes) checks unkeyed whole-stream formats over more routes and stem choices; this record answers the separate keyed question.

## Reproduce

We ran the [pinned Stage N source](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_n.py) at commit `bf89d3d`; its 456-row TSV matches the pinned repository byte-for-byte. The bundled [numerical input profile](experiments/records/wulfic-grid-native-keys/source-profile.json) records the exact key streams and unigram distribution exported from that checkout; no upstream source code is copied. The site’s own 256-cell [grid export](exports/alphanumeric-grids.csv) independently reproduces every source grid byte and base-60 digit.

With Python's standard library, run from the extracted Liberpedia repository:

```text
python experiments/records/wulfic-grid-native-keys/run.py --check
python experiments/records/wulfic-grid-native-keys/check.py
python experiments/records/wulfic-grid-native-keys/plot.py --check
```

The checker rebuilds the grid, replays every byte operation, and independently calculates all 384 GP29 likelihood scores from the recorded numerical inputs. It also runs the explicitly post-replay planted byte and rune diagnostics. The [plan](experiments/records/wulfic-grid-native-keys/plan.json) pins files, source revision and exact thresholds; `prepare_source.py` regenerates the numerical profile when supplied a matching external checkout.
