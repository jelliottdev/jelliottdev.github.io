# Which archived signed bodies retain trailing whitespace?

The preserved corpus contains trailing spaces and tabs, and copies of the same visible message can disagree about them. A strict census accepts 111 clear-signed files from the 133-path G-02 archive. They contain 67 distinct bodies when exact bytes and line endings count, or 54 when trailing spaces/tabs and dash escaping are removed and line endings are normalized. Sixteen exact bodies have trailing whitespace: 62 lines carry 564 spaces and 278 tabs. Thirteen canonical message groups have copies with different trailing-whitespace count sequences.

This is a preservation result. It does not establish that the counted bytes were an intentional payload or that copies lacking them preserve the original formatting. The signed data blob contributes 221,730 of the 224,213 exact-body lines; the line total is not a sample of independent prose messages.

## What was fixed before counting

The plan uses the existing G-02 content-addressed archive: 89 distinct files mapped to 133 pinned public paths at Dukotah revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. Each input is hash-checked. Parsing requires exact, unindented clear-sign armor, a `Hash:` header and blank separator, and a completed signature block. It preserves leading indentation, whitespace-only body lines, dash escaping and raw line terminators. Hash headers and signature armor are excluded. Armored `PGP MESSAGE` packets remain opaque.

The strict subset omits 22 paths: 11 public-key files, six G-02 NO-SIG cases, four G-02 PASS cases and one FAIL case. Four clear-sign openings fail the explicit header rule; their paths and reasons appear in the result. These exclusions describe this parser's scope, not a revised OpenPGP validity verdict. The accepted 111 paths have saved G-02 PASS verdicts; the full signature corpus was not rerun.

Only the three numeric lists literally present in the source whitespace script were compared against complete or leading nonzero-count sequences: `[5,3,2,2,3,5]`, `[2,3,5,7,11,13,17,19,23,29,31,37]`, and `[137,103,45,14]`. None matched. The last list is copied from the executable source despite a disagreeing number in its label/comment. This narrow comparison does not exclude other encodings, alternate counts or previously known whitespace channels. No binary decode or adaptive cipher search was attempted.

For example, the preserved rune-table copy has counts `[240,200,80,32]`; the preserved 2014 welcome copy has `[2,3,7,11,13,17,23,29,31,37]`. Reporting these observations alongside zero literal-list matches prevents the fixed comparison from becoming a claim that interesting whitespace is absent.

## Controls and interpretation

Seven planted fixtures cover spaces, tabs, whitespace-only lines, dash escaping, leading indentation, LF/CRLF/CR endings, indented armor, opaque packets and malformed boundaries. A separate regex/delimiter checker reconstructs every accepted body and independently compares every nonzero line's counts, the exact hashes and both deduplication totals. Sparse receipts give the line number, suffix pattern and counts for every nonzero line; every omitted line explicitly has zero trailing spaces/tabs.

An isolated GnuPG control verifies one archived PASS message, appends a space and tab to its first nonempty body line, then verifies the edited message under the same public key. Both retain `VALIDSIG` with the unchanged signature. This is expected: [RFC 4880 §7.1](https://www.rfc-editor.org/rfc/rfc4880#section-7.1) excludes trailing spaces and tabs from cleartext signature calculation. A valid cleartext signature therefore cannot authenticate these particular whitespace bytes.

The original source script expects three raw Markdown files absent from the pinned source checkout. This record supplies a newly scoped raw-corpus census; it does not reproduce that unavailable historical scan. The original frozen plan and source code are retained. After the first dense report exceeded 108 MB, a documented reporting amendment stored only nonzero line receipts with explicit zero defaults and line-ending totals. The corpus, parser rules, numeric comparisons and measurements remained the same.

## Reproduce

From the repository root:

```text
python experiments/records/dukotah-h02-raw-whitespace-census/run.py --check
python experiments/records/dukotah-h02-raw-whitespace-census/check.py --gpg-control
```

Python 3 standard library suffices for the census and independent checker. The optional signature control requires GnuPG and imports only the archived public key into a temporary isolated home. The next useful evidence is an independently preserved original byte copy of a discrepant message, with provenance; a valid signature alone cannot choose its original trailing whitespace.
