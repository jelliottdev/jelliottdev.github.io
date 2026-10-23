# Do the runes directly form file bytes?

**No recognizable file beginning or complete printable text emerged** from three fixed encodings of the LP2 rune stream. This is a baseline for the suggestion to pack rune values as bytes, not a test of every possible encoding.

The input is each nonempty page of [LP2](#/pages) from 00 through 55, plus the pages joined in their printed order. The script tries three direct conversions: five bits per rune index in ordinary bit order, five bits with each token reversed, and one byte per Gematria Primus prime value. These are deliberately simple rules that can be replayed without guessing a format after viewing the output.

![Results for three direct rune encodings; no full printable text or chosen file prefix.](experiments/records/rune-direct-byte-packing/packing-screens.svg)

There are **56 targets** (55 nonempty pages and one joined stream), making **168 encoded streams**. None is entirely printable ASCII (allowing tab and line breaks). None begins with a PNG, gzip, ZIP, PDF, ELF or Windows MZ signature. The two five-bit encodings also fail strict whole-stream UTF-8 on every target.

The prime-byte encoding passes the UTF-8 *syntax* screen on all 56 targets for a trivial reason: every GP prime is at most 109, so each is an individually valid one-byte ASCII code. The encoded streams contain control bytes and fail the printable-text screen. Calling that a text decoding would be misleading.

## What this settles

Under these exact page boundaries and direct conversions, the runes do not already look like complete ordinary text or one of the six specified file starts. A header match, had one occurred, would still need a full format parser before it could count as a file. No bytes were executed.

This experiment does **not** test word-level prime sums, another bit width or byte order, transformed or compressed data, a header later in the stream, or selecting a different reading order. Those choices change the search space and need their own declared rule and control.

## Reproduce

Download this experiment's ZIP or run from the repository root:

```text
python experiments/records/rune-direct-byte-packing/run.py --check
python experiments/records/rune-direct-byte-packing/check.py
```

The [result file](experiments/records/rune-direct-byte-packing/results.json) lists each target, conversion, byte count, first eight bytes and stream hash. The second script independently rebuilds the streams from the page records. Both use Python's standard library only.
