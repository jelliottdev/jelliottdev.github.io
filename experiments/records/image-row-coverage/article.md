# Can image-only detection find every rune row?

This fixed detector does not reliably recover individual rune rows across the eight selected page layouts. It proposes 83 image bands; 43 match the 65 manually annotated rune rows under the frozen one-to-one interval rule. This is a segmentation control, not evidence of an omitted line in the archive.

The computation, independent check and visual review are preserved with this experiment. They establish the behavior of this fixed detector on the selected images; they do not certify the transcription.

## What was tested

The source lead is Dukotah/cicada3301 at revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`, specifically `liber-primus/analysis/transcription/linecrop.py`. Its row-detection helper operates on the image alone; the later command-line mapping uses canonical rows. We implemented the fixed image-only rule separately rather than executing downloaded code.

The protocol and manual image reference were frozen before detector execution. The detector examines the central 22–78% of each image. Pixels darker than grayscale 128 contribute to the horizontal projection. A scanline is active when more than 1% of the examined columns are dark. Contiguous active intervals shorter than 20 pixels are discarded before remaining intervals separated by fewer than 12 pixels are merged. No thresholds were tuned after seeing these results.

A proposal matches a reference interval when their intersection divided by their union is at least 0.5. Maximum-cardinality one-to-one matching prevents a large band from counting as several recovered rows. The result retains all eligible edges, matching alternatives and omission controls.

## Results and overlays

| Page | Reference rune rows | Image proposals | Matched rune rows | Overlay |
| --- | ---: | ---: | ---: | --- |
| LP2-00 | 12 | 12 | 9 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-00.svg) |
| LP2-03 | 11 | 6 | 4 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-03.svg) |
| LP2-15 | 8 | 11 | 5 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-15.svg) |
| LP2-31 | 12 | 12 | 12 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-31.svg) |
| LP2-39 | 12 | 12 | 9 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-39.svg) |
| LP2-50 | 0 | 13 | Not applicable | [Inspect](experiments/records/image-row-coverage/overlays/lp2-50.svg) |
| LP2-56 | 5 | 10 | 2 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-56.svg) |
| LP2-57 | 5 | 7 | 2 | [Inspect](experiments/records/image-row-coverage/overlays/lp2-57.svg) |

LP2-50 contains alphanumeric rows in this inventory, not rune rows. It is a non-runic control, not a zero-percent rune-recovery result.

Every overlay preserves the source JPEG beneath the annotations. Orange R brackets identify reference rune rows, gray N brackets identify other text rows, and blue D rectangles identify image-only proposals. Visual inspection classified all 83 proposals: 43 individual rune rows, 24 non-runic text rows, seven bands spanning multiple rune rows, and nine artwork bands. No reference interval was changed after detection. These categories describe visible regions; they do not identify precisely which pixels caused a merge.

The numerical count alone is insufficient: LP2-00 has 12 proposals and 12 reference rune rows, yet only nine match. Artwork and merged rows can conceal each other's count discrepancy.

## Omission controls and limits

Each of the 65 reference rune rows is separately treated as absent from a hypothetical candidate inventory while the image and its proposals remain unchanged. The report records whether that row can or must receive a match across all maximum matchings. These are deterministic coverage checks on shared images, not 65 independent trials or 65 actual transcription errors.

An inventory-only comparison cannot visit a row omitted from that inventory by construction. That comparison illustrates a coverage restriction; it does not reproduce the source repository's classifier or measure its accuracy.

The pages were selected for different layouts, not randomly sampled. The reference intervals are approximate manual body intervals and prior familiarity with pages is disclosed. Human review remains pending. This experiment does not recognize rune identities, audit within-row insertions or deletions, certify all 75 pages, or show that an archive row is missing.

## Reproduce

Extract the reproduction bundle and original-images.zip into the same root, or use the repository. With Python 3 and Pillow 11.3.0, run `python experiments/records/image-row-coverage/run.py --check` from the root. This reproduces the saved results and all eight overlays in a temporary directory and runs the independent check. To retain new output, use `--output row-replay` instead.

For the individual stages, choose output paths that do not exist:

```sh
python scripts/test_image_row_matching.py
python scripts/image_row_coverage.py --output row-results.json
python scripts/check_image_row_coverage.py row-results.json --receipt row-audit.json
python scripts/render_image_row_coverage.py row-results.json row-audit.json --output row-overlays
```

The producer checks the frozen plan, reference and image hashes. The independent checker uses scalar pixel bytes, regular-expression active runs, rational interval arithmetic and exhaustive matching enumeration without importing the producer. Both use Pillow to decode the JPEGs, so decoding is a shared dependency. The matching unit controls exhaust all 512 bipartite graphs with three vertices on each side.

`results.json` is the untouched first-run report; its status describes the state at computation time. `audit.json` supplies the subsequent independent computational check. `overlay-review.json` records the later visual review and hashes of all eight overlays. Do not edit the first report to imply that review occurred before it was produced.

Future variants should change one declared segmentation assumption at a time and retain this baseline. More permissive matching alone is not evidence of better row detection.

## Related explanations

See [transcription checking](#/wiki/transcription-checking?section=coverage-limits) for the difference between a recorded correction and complete review, and [search spaces and bounds](#/wiki/search-space) for why a result applies only to the declared test.
