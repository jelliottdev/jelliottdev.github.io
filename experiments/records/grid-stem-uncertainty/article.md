# The ten bare stems in the LP2-49–51 grids

**Ten of the 256 grid entries contain a character shaped like a bare vertical stem.** The current wiki text writes that character as either uppercase `I` or lowercase `l`. The preserved page images show no dot or horizontal foot at these positions, so the shape alone does not settle the case. Six of the ten positions agree across the two preserved text transcriptions; agreement does not turn an indistinguishable shape into a verified character.

This is an **input audit**, not a proposed LP2 decryption. It supplies exact coordinates and a bounded sensitivity calculation for readers who convert the two-character entries into bytes. It does not change the published transcription silently.

## Locate the marks

Grid rows begin at the first alphanumeric row on each page, excluding any runic lines. Columns run left to right from 1 to 8. The diagram maps the ten stems and, in tan, the separate `2S`/`2s` transcription disagreement. Select it for the complete SVG, and inspect the [LP2-49](#/reader/lp2-49), [LP2-50](#/reader/lp2-50), and [LP2-51](#/reader/lp2-51) images before choosing a reading.

![Ten bare-stem positions mapped across the three eight-column grids; one separate S/s disagreement is marked.](experiments/records/grid-stem-uncertainty/stem-map.svg)

| Page | Row, column | Seventh-onion text | Wiki text | If `I` | If `l` |
| --- | --- | --- | --- | ---: | ---: |
| LP2-49 | 1, 3 | `2l` | `2l` | 138 | 167 |
| LP2-49 | 4, 2 | `3I` | `3I` | 198 | 227 |
| LP2-49 | 6, 6 | `1L` | `1l` | 78 | 107 |
| LP2-49 | 7, 3 | `0L` | `0l` | 18 | 47 |
| LP2-50 | 2, 3 | `3I` | `3I` | 198 | 227 |
| LP2-50 | 11, 6 | `0l` | `0I` | 18 | 47 |
| LP2-50 | 12, 8 | `0I` | `0I` | 18 | 47 |
| LP2-50 | 13, 7 | `2l` | `2l` | 138 | 167 |
| LP2-51 | 2, 8 | `0l` | `0l` | 18 | 47 |
| LP2-51 | 8, 7 | `3i` | `3I` | 198 | 227 |

The last two columns use the **conditional** digit order `0–9`, `A–Z`, `a–x` and the rule `byte = 60 × first digit + second digit`. They are not a claim that the manuscript intended base 60 or bytes. Changing `I` to `l` adds 29 to the value at every listed cell, but the number of changed bits depends on the first digit. The [full JSON report](experiments/records/grid-stem-uncertainty/results.json) keeps all coordinates, both values and the bit differences.

The `1L` and `0L` readings in the seventh-onion text would require an uppercase L with a foot; that foot is not visible in these image locations. The `3i` reading would require a dot; none is visible there. These observations constrain the historic transcriptions without deciding between `I` and `l`. At LP2-50 row 12, column 5, the distinct `2s`/`2S` disagreement is **not** a bare-stem case. In a close view, both preserved JPEG versions appear to show uppercase `S`; this remains a visual judgment for human review. The [five-source-difference guide](#/wiki/seventh-onion-transcriptions?section=grid) retains both text readings.

## What changes if the ten cases remain open?

Starting from the wiki's 256 tokens, the script changes **only** these ten second characters. Each may be `I` or `l`, giving `2^10 = 1,024` complete inventories. The other 246 entries, including `2S`, remain fixed. This is a sensitivity envelope, not a claim that all 1,024 combinations are equally plausible. A consistent font or a future source could constrain several together.

| Inventory measure | Current wiki text | Range across 1,024 variants |
| --- | ---: | ---: |
| Distinct two-character tokens | 161 | 160–163 |
| Set bits in the 256 conditional bytes | 1,017 | 1,006–1,026 |
| Even-valued conditional bytes | 134 | 129–139 |

The widely cited **161 distinct tokens** is therefore a property of one transcription, not an image-settled invariant. A later analysis that depends on exact token equality, a checksum, a bit image, or a route through these cells should specify its readings and rerun under relevant alternatives. This audit does not test any route or candidate plaintext.

## Reproduce and review

From the repository root, use Python 3's standard library. If using the experiment ZIP, also extract [original-images.zip](downloads/original-images.zip) into the same folder before running the scripts; the experiment ZIP names and hashes its required page JPEGs but keeps those large images in the shared download.

```text
python experiments/records/grid-stem-uncertainty/run.py --check
python experiments/records/grid-stem-uncertainty/check.py
```

The first script verifies SHA-256 hashes for the wiki grid export, archived text and both preserved JPEG copies for each page, then enumerates every one of the 1,024 variants. The second rebuilds the 256 entries from the structured page records and independently checks every saved variant and metric. These checks verify the arithmetic and provenance; a person must still inspect the image shapes. The image files are preserved at [wiki LP2-49](images/lp2-49.jpg), [LP2-50](images/lp2-50.jpg), [LP2-51](images/lp2-51.jpg), and the [seventh-onion source collection](#/wiki/2014-seventh-onion?section=download).

The enumeration does **not** cover `0`/`O` or all conceivable glyph ambiguities, changes in numeral base, or the separate `2S`/`2s` choice. It also does not establish that independently changing the ten cases is typographically natural. Its purpose is to prevent a downstream result from being reported as robust merely because two text sources agree at a visually ambiguous stem.
