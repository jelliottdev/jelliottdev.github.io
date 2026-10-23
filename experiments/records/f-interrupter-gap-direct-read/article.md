# Can the gaps between F runes be read directly?

The suggestion that F/Fehu *locations* carry a separate message has several possible meanings. This test fixes one narrow one: **take every gap between consecutive F runes and read its number directly as a Gematria Primus rune index or prime value.** It does not skip awkward gaps or reduce them modulo 29.

**None of the four literal readings produces a complete symbol stream.** LP2-00–55 has **458 F runes**, making **457** consecutive gaps when pages are joined or **403** when each page starts afresh. Every direct mapping leaves values outside its 29-symbol alphabet.

![Four natural direct readings of the 403 within-page F gaps each leave unmapped values; an additional encoding rule would be needed.](experiments/records/f-interrupter-gap-direct-read/gaps.svg)

| Gap number and symbol map | Within-page gaps mapped | Joined-page gaps mapped |
| --- | ---: | ---: |
| Position distance → zero-based index 0–28 | 273 / 403 | 287 / 457 |
| Position distance → exact GP prime | 157 / 403 | 172 / 457 |
| Runes *between* Fs → zero-based index 0–28 | 281 / 403 | 296 / 457 |
| Runes *between* Fs → exact GP prime | 140 / 403 | 150 / 457 |

“Position distance” subtracts the two F rune positions. “Runes between” is that distance minus one. For example, the second and third Fs in the joined stream are **41** positions apart. That cannot be a zero-based GP index, which must be 0–28. The largest observed position distance is **218**. All gaps, including cross-page gaps in the joined version, remain in the [full result](experiments/records/f-interrupter-gap-direct-read/results.json) with both source F ordinals and page labels. Unmapped values remain explicit `null` entries in the ordered symbol vectors; no attractive fragment is selected from the mapped subset.

This result says that those **four direct conventions** need an extra coding rule to make a complete reading. It does not reject an F-location message in general. Positions rather than gaps, F/non-F bits, variable-length numbers, deliberate nulls or a key could encode something else. The [59-Fehu coordinate replay](#/experiments/fehu-coordinate-triad) tests a different rule that deliberately reduces selected offsets modulo 29; its result cannot be counted as a direct-gap reading. The [F-deletion lag test](#/experiments/f-delete-lag13) asks about rune repeats after deletion, also a different question.

## How the count was made

The test keeps exactly the 29 GP runes from each LP2-00–55 transcription, including headings, and drops punctuation and spaces. It stores the page-local and joined-stream position of every F. A joined stream includes 54 gaps crossing page boundaries; the within-page version omits those gaps. A number maps only when it literally equals a zero-based index from 0 to 28 or one of the 29 GP prime values. No modulo, wrap, skipped value or chosen page subset is used.

Two synthetic streams place Fs at known positions so their distances map to the first GP prime symbols and to known GP index symbols. An out-of-range control stays unmapped. The independent checker rebuilds all 458 positions from per-page JSON text, compares its rune streams with the archived text files, and verifies every gap and mapped/unmapped position.

From the repository root:

```text
python experiments/records/f-interrupter-gap-direct-read/run.py --check
python experiments/records/f-interrupter-gap-direct-read/check.py
```

The [plan](experiments/records/f-interrupter-gap-direct-read/plan.json), [results](experiments/records/f-interrupter-gap-direct-read/results.json) and [checker](experiments/records/f-interrupter-gap-direct-read/check.py) pin the exact scope. This is a newly defined bounded reading of a broad idea, not a replay of a historical decoding attempt.
