# The same six runes on LP2-27 and LP2-55

**`ᛞᛄᚢ-ᛒᛖᛁ` appears once on each of these two pages.** The six runes are conventionally transliterated `DJU-BEI`; the hyphen is a visible separator and does not count as a rune. In the archived text they begin at rune offset **28 on LP2-27** and **70 on LP2-55**, counting from zero at the start of each page.

![The same six-rune DJU-BEI sequence appears at zero-based offsets 28 and 70 on LP2-27 and LP2-55.](experiments/records/dju-bei-cross-page/offsets.svg)

| Page | Where to look | Zero-based rune offset | One-based rune position | Exact source slice |
| --- | --- | ---: | ---: | --- |
| [LP2-27](#/reader/lp2-27) | line 2, columns 11–17 | 28 | 29 | `ᛞᛄᚢ-ᛒᛖᛁ` |
| [LP2-55](#/reader/lp2-55) | line 4, columns 4–10 | 70 | 71 | `ᛞᛄᚢ-ᛒᛖᛁ` |

The offset counts only the 29 Gematria Primus runes. Spaces, hyphens, punctuation and row ends are skipped, but the page's rune order is preserved. The count resets at each page. Thus this verifies the two locations reported in the supplied discussion without relying on an ambiguous character count that includes separators.

The recurrence is a **source observation**, not a decryption. It does not show that the phrase is plaintext, that one page supplies a key to the other, or that it explains suppressed doublets. The match was already known before this audit, so we do not attach a chance probability to it. This record checks these two stored transcriptions only; it does not claim a manuscript-wide search or fresh adjudication against the page images.

To reproduce, run `python experiments/records/dju-bei-cross-page/run.py --check` from the repository or extracted experiment bundle. The [script](experiments/records/dju-bei-cross-page/run.py) reads the archived [LP2-27](data/pages/lp2-27.json) and [LP2-55](data/pages/lp2-55.json) page records, checks their rune counts, and verifies the stored [coordinate report](experiments/records/dju-bei-cross-page/results.json). Compare the [original LP2-27 image](images/lp2-27.jpg) and [LP2-55 image](images/lp2-55.jpg) if a proposed interpretation depends on the exact visual form or adjacent marks.
