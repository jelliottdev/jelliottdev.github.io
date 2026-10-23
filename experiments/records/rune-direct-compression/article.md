# Do directly packed LP2 runes form compressed data?

**No complete compressed stream was found** under five specified formats. We reused the exact **168 byte streams** from the [direct rune-to-byte test](#/experiments/rune-direct-byte-packing): 55 nonempty LP2 pages plus their joined stream, each encoded as high-bit-first five-bit rune indices, reversed-token five-bit indices, or one-byte GP primes. We tried zlib, gzip, raw DEFLATE, bzip2 and XZ at byte zero. All **840** decoder attempts returned invalid; none reached the output-size cap.

![Five compression formats each have zero valid complete streams among 168 fixed rune-to-byte streams.](experiments/records/rune-direct-compression/summary.svg)

The earlier record checked printable text, UTF-8 and file *beginnings*. This follow-up runs actual decompressors and requires a **complete** stream. A successful-looking prefix would not qualify: the decoder must reach its end marker, consume all input, and produce at most 1 MiB. We record invalid, incomplete, trailing-junk and output-limit states separately; an output-limit result would remain unresolved, not count as a failed decompression. None occurred in these manuscript inputs.

The byte construction is fixed before decompression. Five-bit modes encode each zero-based rune index in five bits, optionally reversing bits within each token, then append only the zero bits needed to finish the last byte. The third mode stores each GP prime as one unsigned byte. Page joins are permitted only for the one declared LP2-00–55 combined stream. We did not scan offsets, prepend signatures, change page order or try alternate widths.

Each format passed a known compressed-message control, a truncated-stream rejection, a trailing-junk rejection and a synthetic expansion beyond 1 MiB. One extra end-to-end control uses **16 valid rune indices** packed with the exact five-bit rule to form a complete zlib stream decoding to `a0`. That shows the rune packing and the decoder can work together; it does not imply the manuscript should use zlib. An independent checker rebuilds every byte stream from the per-page JSON transcription, checks its SHA-256 against the earlier record, and rechecks all 840 outcomes.

This result rules out these five *direct, byte-zero, complete-stream* readings of this transcription. It does not test compression after a cipher layer, an offset, a changed packing, a dictionary, reordered pages, or other compression formats. Even a valid decompression would need separate analysis before being called a reading.

From the repository root, run:

```text
python experiments/records/rune-direct-compression/run.py --check
python experiments/records/rune-direct-compression/check.py
```

The [plan](experiments/records/rune-direct-compression/plan.json), [results](experiments/records/rune-direct-compression/results.json) and [independent checker](experiments/records/rune-direct-compression/check.py) state and reproduce the exact bounds.
