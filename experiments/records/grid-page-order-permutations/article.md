# Is the LP2 byte grid a page-order table?

One published proposal asks whether a consecutive part of the 256-byte LP2-49–51 grid is a permutation of page indices **0–55** or **0–56**. That is a precise test: every byte in such a window must be in range, and each page index must appear once. We found **no matching window** in the source's saved byte stream or in 16,384 fixed grid readings that account for ten disputed `I`/`L` stems.

![The longest run of eligible page-index bytes is five, far shorter than the 56 or 57 needed](experiments/records/grid-page-order-permutations/page-order.svg)

The simpler reason for the null result is useful: the longest uninterrupted run containing only values 0–55 is **three bytes** across the tested readings; allowing value 56 raises the maximum to only **five bytes**. A 56- or 57-byte permutation cannot occur without a run at least that long. The source's own pinned 256-byte file has a maximum run of three under either range.

## Fixed search

The original E-02A proposal scans every 56-byte window of its saved 256-byte `canon_256.bin`; it also reports a 57-byte 0–56 variant. We replayed both on that exact file, then used the current page transcription's conditional base-60 conversion and the same 16 row/column routes and 1,024 `I`/`L` stem readings as the [direct-byte study](#/experiments/grid-direct-bytes). The source file and current printed-order conversion differ at **three byte positions**; they are not silently treated as identical.

| Input | 56-byte windows | 57-byte windows | Longest eligible run | Matches |
| --- | ---: | ---: | ---: | ---: |
| Published source byte file | 201 | 200 | 3 | 0 |
| 16,384 grid readings | 3,293,184 | 3,276,800 | 5 (for 0–56) | 0 |

The scanner first checks the necessary value range in every window, then checks for a one-of-each permutation. Synthetic streams with deliberately planted 0–55 and 0–56 windows are detected at their planted offset. An independent check reconstructs the readings and verifies the longest eligible runs without using the window scanner.

## What the result means

This excludes a **literal contiguous page-index table** in the declared byte readings. It does not test arithmetic transforms, encryption, noncontiguous selections, a different page count or a different transcription. The quoted page-order interpretation is a hypothesis about how the grid might guide reading; no page route or decoded text was claimed by this result.

## Reproduce

Extract this experiment and the reference-data bundle together, then run:

```sh
python experiments/records/grid-page-order-permutations/run.py --check
python experiments/records/grid-page-order-permutations/check.py
```

Both use Python's standard library. The [complete results](experiments/records/grid-page-order-permutations/results.json) give route-level maximum runs and counts.
