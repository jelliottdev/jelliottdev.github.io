# LP2-32 grid sums and the 2016 message

This recount reproduces three numerical equalities: **563, 569 and 1136**. They are the first-row sum, first-column sum and central 5×5 perimeter sum of a specified arrangement of LP2-32. The preserved 2016 image measures 563×569 pixels, and its extracted payload contains 1,136 bytes.

“Supported” refers to these exact calculations. It does not establish that the correspondence was intended, statistically unusual or useful for decryption.

## Construct the grid

Use the archived LP2-32 text. Keep all 121 alphabet runes, remove separators, and place the stream left-to-right into eleven rows of eleven. Do not reverse, rotate, pad or omit runes. Replace each rune with its stored Gematria Primus prime value.

This is an analytical rearrangement. It is not a claim that the original manuscript has eleven printed lines. The JSON records every grid cell, its original rune ordinal and its source-text character offset so the rearrangement can be followed back to the page.

## Exactly which cells are summed?

The first row is grid row 1, columns 1–11. The first column is column 1, rows 1–11. They share the top-left cell, so these measurements are not disjoint.

The central 5×5 block occupies rows 4–8 and columns 4–8, using one-based coordinates. Sum its outer border, counting each corner once. That is 16 cells: five across the top, five across the bottom, and three additional cells down each side. Do not include the central nine cells or count corners twice.

In the enlarged figure, the top border sums to 275 and the bottom border to 373. The three remaining left-edge cells sum to 231; the three remaining right-edge cells sum to 257. Thus `275 + 373 + 231 + 257 = 1136`. This decomposition counts each corner exactly once.

| Quantity | Value |
| --- | --- |
| Rune count | 121 |
| Sum of all 121 prime values | 6045 |
| First row | 563 |
| First column | 569 |
| Central 5×5 perimeter | 1136 |
| Original 2016 JPEG width × height | 563 × 569 |
| Preserved OutGuess payload bytes | 1136 |

The output also lists all eleven row sums, all eleven column sums and all 49 placements of a contiguous 5×5 block within this grid. Only the central block has perimeter sum 1136 under these rules. That statement concerns those 49 placements; it is not a chance probability over other layouts, page choices or target numbers.

## What was compared with the grid?

The image measurement comes from the original JPEG frame header, not a displayed preview. Payload length means raw bytes in the preserved extracted signed message, including its armor and formatting. It does not mean visible characters, plaintext letters, pixels or the JPEG file size.

The [later-message guide](#/wiki/later-messages) separately documents an exact OutGuess extraction and signature verification. This recount uses those preserved bytes and hashes them; it does not need to run OutGuess again. The [Wing and Tree guide](#/wiki/wing-and-tree) locates the manuscript drawing. A numerical match does not prove that the two tree images have the same source.

## Reproduce

Extract this experiment’s ZIP with its directory structure intact. It includes the payload, scripts and text inputs. Download the [original 2016 JPEG](images/message-2016.jpg) separately and save it as `images/message-2016.jpg` inside the extracted folder. The ZIP’s image-input manifest gives its checksum. Python’s standard library is sufficient.

```text
python experiments/records/lp2-32-message-grid/run.py --check
python experiments/records/lp2-32-message-grid/check.py
```

The producer reads the rune text and parses JPEG segment headers. The checker reads the separate archived page record, uses flat-index cell sets to recount the perimeters, and checks the image’s baseline frame header independently. Both use the same stored alphabet, so their agreement does not independently resolve transcription ambiguities.

## Limits and follow-up

The original lead selected this page, arrangement and central border for inspection. No null model or accounting for other explored arrangements is supplied here. A follow-up can test a stated family of layouts or a fixed shuffle model, but should not describe this one successful comparison as an exhaustive search. See [search space and bounds](#/wiki/search-space) and [null models](#/wiki/null-models).

## Recreate the diagram

The SVG is included in the experiment ZIP. The drawing reads the stored cell ledger directly; its numbers are not manually retyped. Install Matplotlib if you want to recreate it, then choose a new output filename:

```text
python experiments/records/lp2-32-message-grid/plot.py --output my-grid.svg
```

The drawing script refuses to overwrite an existing file. Plotting is optional; the producer and independent checker still use only Python’s standard library.
