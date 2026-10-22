# LP2-49–51: do the grid entries directly form a text or file?

**None of the 16,384 byte streams in this bounded test passed a whole-stream ASCII or UTF-8 screen or began with one of the four specified file headers.** This rules out a straightforward reading of the grid under these particular byte and traversal rules. It does not rule out a different encoding, a later transformation, or a file header elsewhere in a stream.

The [LP2-49–51 grid](#/wiki/alphanumeric-grids) has 256 two-character entries. If each is read as one byte using the declared base-60 digit order `0–9, A–Z, a–x`, the most immediate question is whether those bytes already say something. This test checks that question without choosing a route after seeing the output. Base 60 is **conditional** on the one-byte and digit-order assumptions; neither is established as the intended interpretation.

## What was tested

The 10 rows on [LP2-49](#/reader/lp2-49), 13 on [LP2-50](#/reader/lp2-50), and 9 on [LP2-51](#/reader/lp2-51) are joined in that order into a 32 × 8 rectangle. Each pair becomes `60 × first digit + second digit`, with no wrapping or omitted entry. The [ten bare-stem audit](#/experiments/grid-stem-uncertainty) supplies the only transcription alternatives: `I` or `l` in ten fixed cells. All 1,024 settings are tested; the other 246 entries, including the separate `2S` cell, stay as in the wiki transcription.

For both row-wise and column-wise reading, the script varies the outer direction, initial inner direction, and whether the inner direction alternates after each row or column. Those three binary switches make eight routes per axis, or **16 complete routes**. Each visits every cell exactly once. The complete scope is therefore `16 × 1,024 = 16,384` streams of 256 bytes each.

![Six direct-format screens across sixteen complete grid routes; all cells show zero matches among 1,024 stem settings per route.](experiments/records/grid-direct-bytes/route-screen.svg)

The labels in the chart encode the three switches: outer reverse, initial inner reverse, and alternation, with `0` for forward/constant and `1` for reverse/alternate. A cell counts how many of the 1,024 stem settings pass that screen. Its zeroes concern only the screen named at the column top.

| Screen | Exact acceptance rule | Passing streams |
| --- | --- | ---: |
| ASCII text | Every byte is printable ASCII or tab, LF, or CR | 0 |
| UTF-8 text | Strict UTF-8 decoding accepts all 256 bytes | 0 |
| PNG | First eight bytes equal the [PNG signature](https://www.w3.org/TR/png-3/#5PNG-file-signature) | 0 |
| gzip | First three bytes are `1f 8b 08`, including compression method 8 ([RFC 1952](https://www.rfc-editor.org/rfc/rfc1952.html)) | 0 |
| ZIP | First four bytes are the local-file signature `50 4b 03 04` ([PKWARE APPNOTE](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)) | 0 |
| zlib | First two bytes satisfy CM=8, CINFO≤7 and the modulo-31 header check ([RFC 1950](https://www.rfc-editor.org/rfc/rfc1950.html)) | 0 |

A header match would have been a **candidate for further validation**, not proof of a working file. UTF-8 validity would not by itself establish meaningful language. No stream reached either threshold here. The two text screens require the *entire* stream to pass; they do not inspect short readable fragments.

## Reproduce it

Download this experiment's ZIP from the record, or run these commands from the repository root:

```text
python experiments/records/grid-direct-bytes/run.py --check
python experiments/records/grid-direct-bytes/check.py
```

The first script pins the SHA-256 hashes of the grid export and ten-stem register, then recomputes every case and the [JSON report](experiments/records/grid-direct-bytes/results.json). That report retains each route, ten-bit mask, stream hash, first eight bytes and six outcomes. The independent checker rebuilds the entries from the page records, replays every route and mask, and tests positive synthetic controls for all six screens. Both use only Python's standard library and make no network or AI calls.

This result says nothing about a 16 × 16 reflow, a different digit assignment, other glyph uncertainties, a header at a nonzero offset, XOR, compression without one of these headers, or bytes embedded in a larger construction. Those are distinct tests with their own search spaces. The useful stopping point here is narrower: **a direct 256-byte text or one of these four offset-zero file starts does not emerge from these 16 routes and ten stem choices**.
