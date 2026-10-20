# Historical Emerson book-cipher control

## Purpose and what this does not test

A book cipher needs a source edition and counting conventions, not just a book title. This record reproduces the documented 2014 opening-image coordinates against the frozen Emerson Self-Reliance PDF derivative. It gives newcomers a working control and a trace they can inspect before proposing new book-cipher experiments.

**The answer was known before this rerun.** This is a historical replication, not blind discovery, an independent confirmation of source selection, or a decipherment of an unsolved manuscript page. No hidden-service address was visited.

## Frozen plan and prior reconstruction history

The rerun plan and wrapper were committed as `1f67f70` before this execution. Source files, the existing lookup script and the known result were hashed in the plan. An earlier reconstruction had corrected the treatment of embedded verse after inspecting mismatches: the verse remains inside prose paragraph 36 rather than creating extra paragraphs. That earlier adjustment is disclosed in the existing evidence manifest and is not presented here as a rule discovered independently.

The PDF is the contemporary snapshot linked in the historical walkthrough. Its hash is fixed, but the original creator's exact edition is not authenticated by this reproduction.

## Counting conventions

Re-extract the pinned PDF with pypdf 6.19.0 in layout mode. Begin at the first prose paragraph, exclude numeric page footers, and use four-space prose indentation to begin paragraphs. Seven-space verse remains in its surrounding paragraph. Apply Unicode NFKC normalization and join wrapped lines according to the stored extraction rule. All 50 extracted paragraphs must match the frozen derivative.

Coordinates are one-based paragraph:sentence:word:letter positions. Sentences split at `.`, `!` and `?`; words split on whitespace with edge punctuation removed; only ASCII letters count inside the selected word. Single-character entries are copied literally. These are the documented reconstruction conventions, not a universal natural-language sentence parser.

## Result

The complete trace matches the archived control. Fifteen coordinate lookups and seven literal characters reconstruct:

```
auqgnxjtvdbll3pv.onion
```

This is a historical output string. Reproducing it says nothing about any current service at that name. The supported claim is only that these exact inputs and rules reproduce the recorded trace.

## Complete coordinate trace

| Entry | Printed PDF page | Selected word | Output |
| --- | --- | --- | --- |
| 1:2:3:1 | 1 | always | a |
| 3:3:13:5 | 2 | genius | u |
| 45:5:2:3 | 19 | acquires | q |
| 20:3:20:5 | 9 | among | g |
| 8:3:8:6 | 5 | action | n |
| 48:5:14:2 | 20 | experience | x |
| 21:13:4:1 | 9 | justice | j |
| 25:1:7:4 | 12 | truth | t |
| 15:9:3:4 | 7 | above | v |
| 1:1:16:3 | 1 | and | d |
| 4:3:3:1 | 2 | being | b |
| 8:3:26:4 | 5 | daily | l |
| 47:3:3:5 | 19 | equality | l |
| 3 | Literal | Copied directly | 3 |
| 13:2:5:4 | 6 | corpse | p |
| 1:4:16:4 | 1 | private | v |
| . | Literal | Copied directly | . |
| o | Literal | Copied directly | o |
| n | Literal | Copied directly | n |
| i | Literal | Copied directly | i |
| o | Literal | Copied directly | o |
| n | Literal | Copied directly | n |

The first coordinate, 1:2:3:1, selects the third word of the second sentence in paragraph 1: `always`. Its first letter is `a`. The JSON output includes each full selected sentence, so a reader can check the counting rather than trusting the final string alone.

## Reproduce from files

Use Python 3.12.10 and pypdf 6.19.0. Install the exact dependency in your preferred environment:

```
python -m pip install pypdf==6.19.0
python experiments/records/emerson-book-cipher-control/run.py --check
```

Dependency installation needs package access; the actual experiment makes no network request. The wrapper checks every frozen input hash, invokes the existing reproduction script with `--check-pdf`, compares all 50 paragraphs, and checks the complete output trace. It then compares the new report with the saved one. Missing dependencies or changed inputs fail visibly.

To save a separate report:

```
python experiments/records/emerson-book-cipher-control/run.py --output my-emerson-control.json
```

Existing output files are never overwritten. [Download the complete trace](experiments/records/emerson-book-cipher-control/results.json). [Download the pinned PDF](exports/sources/emerson-self-reliance.pdf) and [paragraph derivative](exports/sources/emerson-paragraphs.json). The [coordinate payload](exports/steganography/opening-2014.body.txt) is the extracted message body; extraction and signature verification are separate steps described in the opening-image guide.

For a standard-library-only replay of the frozen paragraphs, run `python scripts/reproduce_emerson.py` without `--check-pdf`. That shorter check does not re-extract the PDF and must not be reported as having done so.

## Retest and review

Codex ran the PDF reconstruction and lookup twice on 20 October 2026. Both produced the same 50 paragraphs and identical complete trace. No counting rule or source changed during this rerun. The diagram was generated afterward from the saved first lookup. Human review remains pending, and the lookup implementation is the existing historical reproduction code rather than a newly independent decoder.

## Family and future variants

A different edition, paragraph convention or source text needs a separate variant with the exact change recorded. An attempt to apply a book cipher to an unsolved LP2 page also needs an independently defined source of coordinates and a success criterion. This historical control is useful for checking an implementation; it does not establish that such a transfer has already been tested.

See [book-cipher conventions](#/wiki/book-ciphers), [Emerson and the historical source](#/wiki/emerson-self-reliance), and [the opening image](#/wiki/opening-2014).
