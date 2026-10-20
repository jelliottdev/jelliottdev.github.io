# Reversing the order of word-like segments

“Read the words backwards” can mean two different operations. You might reverse the runes inside each word, or read the last word first while leaving its runes alone. This experiment tests the second interpretation across each complete page.

The archive gives us rune runs separated by punctuation and line markers. Calling these runs “segments” avoids assuming that they are established plaintext words. The input is LP2-00–55, including headings. LP2-50 has no recognized runes and contributes no candidates.

## What changes?

The [within-segment reversal experiment](#/experiments/lp2-word-reversal) keeps segment order and reverses their contents. Here the contents stay in their original order and the segment order reverses.

Using invented letters as single symbols:

```text
Segments:                 AB | C | D | EF
Reverse inside segments:  BA | C | D | FE  -> BACDFE
Reverse segment order:    EF | D | C | AB  -> EFDCAB
Reverse the whole stream: FE | D | C | BA  -> FEDCBA
```

These are three distinct transformations. Applying both segment-order reversal and within-segment reversal gives whole-stream reversal. That identity helps detect duplicated search coverage; the combined operation does not need to be advertised as a new method.

## Declare the boundaries

| Convention | Rule | Toy input `AB/C-D` followed by a newline and `EF.` |
| --- | --- | --- |
| Split lines | Every non-rune ends the current segment. | Segments AB, C, D, EF produce EFDCAB. |
| Join lines | Ignore slash, carriage return and newline before locating segments; every other non-rune remains a boundary. | Segments ABC, DEF produce DEFABC. |

Hyphens, periods and spaces remain boundaries in both conventions. There is no reversal limited to an individual row: the segment sequence spans the complete page. Headings are not removed, and their segments move with the rest. No additional alphabet substitution is applied.

This record belongs to the reading-route family. Its formal comparison is against the [row/column baseline](#/experiments/lp2-row-column-routes), so multiple scope fields change. For the closer comparison with its within-segment sibling, the pages, boundary rules and nine expected beginnings stay the same; the reversal operation changes.

## Inspect the source trace

![First six LP2-31 output positions under segment-order reversal, showing the last segment read forwards before the preceding segment.](experiments/records/lp2-word-order-reversal/source-trace.svg)

LP2-31 contains 269 runes. Under both conventions its final three-rune segment occupies original rune positions 266, 267 and 268, counted from zero. Those positions appear first and keep their internal order. The next output position jumps back to source rune 258. This is not the sequence 268, 267, 266 that whole-page reversal would produce.

Both conventions agree on these six positions but produce different full outputs. The report retains every source rune ordinal, source character offset and output index. Character offsets refer to Unicode characters in the decoded input, not UTF-8 bytes.

## Findings and limits

| Quantity | Result |
| --- | --- |
| Declared pages | 56 |
| Pages containing recognized runes | 55 |
| Boundary conventions per nonempty page | 2 |
| Completed cases | 110 |
| Distinct full outputs, counted within page | 110 |
| Exact opening comparisons | 990 |
| Matching cases | 0 |

Each case compares its first twelve output rune indices with nine fixed known beginnings: Warning, Welcome, Some Wisdom, the first koan, Loss of Divinity, the second koan, Instruction, LP2-56 and LP2-57. The plan records the exact vectors and hashed source traces.

No case begins with those specified sequences. This does not establish that reversing segment order cannot work: other beginnings, regions and combined ciphers remain untested. There is no general language score or significance test. The [candidate-reading guide](#/wiki/candidate-readings) explains this distinction.

The [page summary CSV](experiments/records/lp2-word-order-reversal/page-summary.csv) includes LP2-50 with zero cases. Counts of distinct outputs do not imply statistically independent evidence.

## Plan and verification

The plan, runner and checker were committed as `0429f5a` before generating the full result. The earlier within-segment and row/column results were already known; this is a declared exploratory follow-up. No boundary or acceptance rule changed after the run.

The runner scans characters to form segments and reverses the list of segments. The checker instead finds regex spans, assigns segment numbers, and sorts positions by descending segment number and ascending position within the segment. It checks all 110 source permutations, full outputs and match decisions, plus source hashes and the reference beginnings. Hand-calculated examples cover both boundary conventions.

For every page and convention, a second check confirms that the new output is the whole-stream reversal of the saved within-segment output. This is an algebraic consistency check, not independent support for a decoding. A complete rerun reproduces the saved report. Review is computational by Codex; human review remains pending.

## Reproduce

Extract the reference-data bundle with its folders intact, or use the repository checkout. From its root, with Python 3:

```sh
python experiments/records/lp2-word-order-reversal/run.py --check
python experiments/records/lp2-word-order-reversal/check.py
```

The summary should report 110 cases, 110 distinct page outputs, 990 comparisons and zero matching cases. All scripts use the standard library and local files.

To save a fresh result without overwriting the reviewed one:

```sh
python experiments/records/lp2-word-order-reversal/run.py --output word-order-rerun.json
```

The destination must not already exist. In each page's `cases`, `segment_lengths` describes the original segment order. `source_ordinals` and `source_character_offsets` give the actual output traversal. `output_indices` contains the full result, not only its opening.

Regenerate the chart and summary CSV from the saved report:

```sh
python experiments/records/lp2-word-order-reversal/plot.py
```

## What would be a new test?

Reversing segment order within each row, excluding headings, choosing other boundaries, or combining reversal with substitution changes the scope. Declare those choices and an acceptance criterion before inspecting outputs. An alternate reading rule should not be judged by whole-stream IoC: every pure permutation preserves it. See [cipher invariants](#/wiki/cipher-invariants) and [planning a follow-up](#/wiki/reproducibility?section=follow-up).
