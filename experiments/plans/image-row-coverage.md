# Image-first row coverage: fixed baseline before measurement

## Question

Can a simple image-only row proposal method detect the text rows that a transcription-driven review might never visit? Measure its actual coverage before treating a missing-row flag as evidence of a transcription error.

This is a proposed bounded control, not a completed manuscript audit. It does not reuse the source repository's reported accuracy or confidence limits. The source helper is inspected, not executed.

## Fixed inputs and selection

Use original JPEGs LP2-00, 03, 15, 31, 39, 50, 56 and 57, with hashes in the JSON plan. This is a deliberately varied convenience set, not a random sample or a representative accuracy estimate. It includes ordinary runic text, decorated layouts, a numeric panel, alphanumeric material and the known final pages. Their appearance and some transcription records have previously been seen; this is not a blinded study.

First annotate each full image directly, without using detected bands to choose regions or the archived line count as a target. Preserve every visible text-like row as runic, non-runic or uncertain, with an original-pixel vertical body interval and rationale. Identify ordinary rune bodies separately from oversized illuminated extensions. Keep illustrations and doubtful marks in a separate region list; do not silently erase difficult regions. Save and hash this visual inventory before running the detector. Annotations are a disclosed reference judgment, not unquestionable ground truth or independent human certification.

## Detector fixed from the inspected helper

The baseline follows `analysis/transcription/linecrop.py` at Dukotah revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`:

1. Decode the JPEG with Pillow and convert to L grayscale; record Pillow version.
2. Consider x in `[floor(0.22W), floor(0.78W))` for every image row, without reading a transcription or its row count.
3. Count grayscale pixels strictly below 128. A row is active when the count is strictly greater than 1% of the selected width.
4. Form contiguous active bands. Discard bands shorter than 20 pixels **before** merging.
5. Merge remaining bands when the gap is strictly smaller than 12 pixels. Preserve original-pixel half-open intervals.

Implement this afresh, including a separate scalar scanner to verify threshold counts and interval boundaries. Do not optimize thresholds after inspecting outcomes. Any alternate width, threshold, merge order or page-specific mask belongs in a later variant. The source helper is a lead, not an established segmentation solution.

## Matching and controls

Match detected bands to the frozen runic-row intervals by one-dimensional intersection-over-union of at least 0.5. Use maximum-cardinality one-to-one matching; retain ties and ambiguous overlaps rather than selecting a favorable labeling. Report unmatched runic rows, unmatched detected bands, matches to non-runic or uncertain regions, and every interval. A large band spanning several rows is not several recovered rows.

After the untouched baseline, remove each annotated runic row in turn from the **candidate inventory**, leaving the image unchanged. The expected missing row remains in the frozen reference. Record whether the image-only detector proposes a matching band for the omitted row. Do not count merely noticing a changed candidate count as detecting the missing image row. Include every row, including those the baseline misses.

The comparison arm visits only regions present in the candidate inventory. It demonstrates the coverage dependency by construction; it is not a reproduction or accuracy estimate of the source repository's full classifier. Do not claim that a classifier labels something incorrectly merely because it was never asked to inspect that region.

Report the untouched baseline's false proposals and missed rows beside omission-control outcomes. Do not pool correlated deletions into a binomial confidence interval. The controls share images and a deterministic detector. A glyph substitution, within-row insertion, transposition, punctuation error or mistaken rune identity is outside this row-coverage test.

## Outputs and publication gate

Retain the frozen annotation file, input hashes, image-only detector output, independent implementation check, all control rows and overlays showing accepted and unmatched bands. Produce phone-readable page thumbnails and downloadable full-resolution overlays with the original JPEG available separately. Do not alter the originals.

Publish only after the independent interval check, inspection of all eight overlays and review of every disagreement. Any correction to the annotation after seeing detector results must be separately recorded with the original retained and both outcomes reported. Do not promote this finite test to certification of all 75 pages or to a claim that a manuscript row is actually missing from the archive.
