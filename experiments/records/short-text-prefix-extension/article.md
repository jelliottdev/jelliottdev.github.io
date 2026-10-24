The earlier scan skipped ten available texts because they were shorter than the full manuscript pattern. Testing the shorter prefixes in those texts found no complete match: the best alignments agreed at **87 of 400** and **37 of 120** word-length positions.

These counts describe compatible lengths, not recovered words. A matching position can be separated from the next matching position by many mismatches.

| Prefix | Newly eligible texts | Manuscript pattern | Shuffle 1 | Shuffle 2 |
|---|---:|---:|---:|---:|
| First 400 words | 8 | 87/400 | 89/400 | 93/400 |
| First 120 words | 10 | 37/120 | 38/120 | 39/120 |

Each score is the best alignment within that short-text search. A complete match would be 400/400 or 120/120.

## What changed

The [earlier archived-text scan](#/experiments/dukotah-held-corpus-skeleton-replay) loaded 94 texts but applied a 2,928-word minimum even to its shorter patterns. This extension uses the same files, parser and fixed first-400/first-120 word patterns. It calls the unchanged scanner separately for each prefix width, admitting eight previously omitted texts for 400 words and ten for 120.

The manuscript parser uses the first 55 percent-separated source segments. Its word lengths count encoded runes, including the source's multigraph convention. The interval rule accepts a corpus word length between the observed length minus its F-rune count and the observed length. Corpus values remain subject to the source's 1–40 range; pattern groups use observed lengths 1–29.

## Result

Both real-pattern winners occur in `cicada_koans_and_lp_sections.txt`: the 400-word prefix at zero-based word offset 141, and the 120-word prefix at offset 40. Two fixed shuffled versions reach 89 and 93 of 400, and 38 and 39 of 120. Two shuffles do not establish a global probability.

The extension scores 5,378 starts per 400-word pattern and 8,037 per 120-word pattern: **40,245 alignment scores** across the real patterns and their four shuffled controls. Counts include the final valid start. All are retained, alongside exact integer recounts, per-text maxima and tie sets. Raw floating-point maxima and the source's selection order are preserved; tiny FFT differences can select among equal integer counts.

This adds alignments within the existing corpus, not new texts. The earlier 84-text real-prefix maxima were 109/400 and 47/120; those separately published results are higher. After verifying identical pattern arrays, combining that saved evidence with this extension covers 92 eligible texts for 400 words and all 94 for 120, with unchanged maxima. The earlier alignments were not rerun here. This is not the historical 224-text scan, an all-window manuscript search, or a test of other editions and word boundaries.

## Checks and reuse

Before the target scan, 37 synthetic cases checked first/final planted starts, exact-width and too-short carriers, random arrays, a 250-word carrier for the 120-word prefix, and constant ties. All 1,371 synthetic alignment scores were independently checked. The six fixed prefixes are dependent patterns, not six independent source passages. After the scan, an independent parser and integer counter verified all 40,245 target scores and every reported selection.

Saved outputs can be checked without retrieving the corpus. Recomputing the scan requires the exact external 94-text inputs and manuscript; [reproduction instructions](experiments/records/short-text-prefix-extension/PORTABILITY.md) explain preparation and temporary-output replay. No third-party corpus text or normalized corpus-length array is redistributed here. The original scanner, parser and pattern-construction source remain unchanged under their retained source license.
