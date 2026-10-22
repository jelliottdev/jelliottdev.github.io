# Where the 86 doublets cross a separator

The standard LP2-00–55 count removes non-runes within each page. That makes some equal runes neighbors in the filtered stream even when a hyphen or row break separates them in the archived text. This audit locates those pairs and tests the site's seven stored LP2 reviewed-text edits.

**Sixty of the 86 pairs are directly adjacent rune characters.** Three have only a row-wrap marker between them, 22 cross a hyphen, and one crosses other punctuation. No doublet crosses an apostrophe alone or with a soft row wrap. These categories are exclusive: a hyphen plus row wrap counts in the hyphen row.

![A bar and legend split the 86 equal-rune pairs by intervening marks: 60 contiguous, 3 row-wrap only, 22 hyphen and 1 other punctuation.](experiments/records/doublet-boundaries/boundaries.svg)

| Intervening marks | Equal pairs | All rune pairs in that class | Rate |
| --- | ---: | ---: | ---: |
| None: rune characters touch | 60 | 9,637 | 0.623% |
| Row wrap only (`/`, CR/LF) | 3 | 388 | 0.773% |
| Apostrophe, perhaps with wrap | 0 | 3 | 0% |
| Hyphen, perhaps with wrap | 22 | 2,721 | 0.809% |
| Other separator | 1 | 152 | 0.658% |
| **All within-page filtered pairs** | **86** | **12,901** | **0.667%** |

The first three rows follow the site's published rune-token convention: slash row markers and physical line breaks are removed, and an internal apostrophe is allowed. Under that convention, **63 of 10,028 within-token pairs** match (0.628%). This is a transcription-based token definition, not an image-verified judgment that every such pair lies within a manuscript word. Conversely, the 22 hyphen-crossing doublets would disappear from a strictly word-internal doublet count. Rates across these groups are descriptive; the small row-wrap and apostrophe groups do not justify a mechanism claim.

## What the stored corrections change

The current archive has separate LP2 reviewed-text layers for pages 05, 07, 11, 15, 35, 37 and 38. They alter notation marks but preserve the ordered rune stream. Applying all seven leaves the **86 pair identities and all five doublet category counts unchanged**. None of the stored punctuation changes falls between a doublet in a way that moves it to another class.

This answers a deliberately limited question. The other LP2 pages have no separate reviewed layer here. The seven layers are not a second complete independent transcription, and this experiment does not recheck 86 pairs against the original 2400×3600 scans. A new rune correction could change both pair identities and counts; a new separator correction could change the word-internal classification without changing 86.

The [full doublet guide](#/wiki/doublets) explains the 86-event count and provides source coordinates. The [transcription guide](#/wiki/transcription-checking?section=coverage) lists which pages have reviewed layers. The [short-lag profile](#/experiments/doublet-lag-profile) keeps the filtered within-page rule and compares equality at rune distances one through five. These analyses answer different questions.

The [EA frequency control](#/experiments/ea-frequency-control) asks a separate question: whether the 86 observed repeat positions are numerically plausible as plaintext EA under one exact running-sum equation. It uses decoded GP indices from solved pages rather than assigning English digraphs by eye.

The [placement audit](#/experiments/doublet-placement) asks whether the event positions cluster by page or sit unusually close together after preserving the number of available within-page edges.

## Reproduce and inspect

Extract the experiment ZIP without flattening folders. Python 3.12 and its standard library suffice:

```text
python experiments/records/doublet-boundaries/run.py --check
python experiments/records/doublet-boundaries/check.py
```

The producer records SHA-256 hashes for the alphabet, all 56 archived page texts, and the seven page records with reviewed layers. `results.json` lists every doublet by page, zero-based rune index, source character offsets, intervening marks and reviewed-layer classification. Run `--write` to regenerate the report and SVG. The independent checker extracts runes with a separate regular-expression path, recounts separator classes, and checks all 86 offsets against the existing source-location ledger. That verifies the archived data handling; it does not authenticate the photographed glyphs.
