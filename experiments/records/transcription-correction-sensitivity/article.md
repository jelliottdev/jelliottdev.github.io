# Do the stored transcription corrections change the published LP2 word-length statistics?

For the **seven currently stored LP2 reviewed-text layers**, no. Applying them all leaves the ordered rune stream, rune-token sequence, 2,896-token length distribution, and whole-stream IoC pair counts unchanged under the site's published counting rule. The one LP1 reviewed layer is a useful positive control: LP1-10 swaps two neighboring runes, changing six ordered-bigram type counts, while retaining its rune multiset and token-length sequence.

This is a sensitivity measurement of the stored layers, **not** a fresh verification of the manuscript images. It says nothing about corrections not yet recorded. A method that treats every punctuation mark as a key reset can change even when this particular word-length statistic does not.

![Per-page correction effects: mark edits, rune order, and rune-token sequence](experiments/records/transcription-correction-sensitivity/correction-effects.svg)

## Inputs and rules

Use the archived `raw` and separate `reviewed_text` in the eight page records: LP1-10; LP2-05, 07, 11, 15, 35, 37 and 38. These are the only eight records with a distinct reviewed layer in the current [75-page inventory](#/wiki/transcription-checking?section=coverage). Every input page record and the 29-rune alphabet are pinned by SHA-256 in `plan.json`.

For word lengths, concatenate LP2-00 through LP2-55 in order, remove slash and CR/LF row wraps, keep headings, and identify runs of the 29 runes with optional internal apostrophes. Other punctuation separates tokens. Count runes, not Latin transliteration letters. This is the same rule used by the [word-length census](#/wiki/word-lengths). No alternative punctuation policy or page-local tokenization is included in the main comparison.

The seven LP2 corrections consist of added or removed notation marks, with no rune substitution. The LP1-10 correction swaps the runes at zero-based rune indices 116 and 117; it is outside the LP2 corpus. The independent checker reconstructs all seven LP2 reviewed strings from the documented edit offsets and checks the LP1 adjacent swap separately.

## Measured effect

| Page | Stored change | Ordered runes | Rune-token sequence | Token count |
| --- | --- | --- | --- | ---: |
| LP1-10 | Adjacent rune swap | Changed | Changed | 40 → 40 |
| LP2-05 | Add `-` | Same | Same | 59 → 59 |
| LP2-07 | Add `.` | Same | Same | 50 → 50 |
| LP2-11 | Add `-` | Same | Same | 55 → 55 |
| LP2-15 | Add `.` | Same | Same | 37 → 37 |
| LP2-35 | Add an apostrophe | Same | Same after omitting the apostrophe | 61 → 61 |
| LP2-37 | Remove three `-` and one `.` | Same | Same | 53 → 53 |
| LP2-38 | Add `.` | Same | Same | 47 → 47 |

Across LP2-00–55, both versions contain **12,956 runes**, **2,896 rune tokens**, and a maximum token length of **14**. Their complete token-length histograms match. Their whole-stream IoC numerator and denominator are **5,787,026 / 167,844,980** in both versions. The ordered rune stream and normalized token sequence have matching SHA-256 values. LP2-35's literal token text contains an extra apostrophe; the apostrophe is not a rune, and its normalized rune token is unchanged.

LP1-10 demonstrates that the audit can register a real ordered-rune difference: the two-rune exchange changes six ordered-bigram type counts. Because it is a swap, its rune count, multiset and whole-page IoC remain unchanged. Its word lengths remain 40 tokens with the same length sequence, even though the token containing the swapped symbols has different rune order.

## What follows—and what does not

For these exact stored LP2 corrections, recomputing the site's joined-page word-length histogram will not change the result. A rune-only frequency or IoC calculation also receives the same symbols in the same order. This is stronger than merely saying that punctuation changes *might* affect word lengths: it measures the actual published corrections under a declared tokenizer.

It does **not** prove that punctuation is irrelevant. A period, hyphen or apostrophe can drive a reset or extraction rule that this experiment does not run. Different tokenization, image-derived separators, or a newly corrected rune can change later measurements. Nor does matching a reviewed layer establish that the image was transcribed correctly everywhere. See [the transcription guide](#/wiki/transcription-checking) for the distinction between archived text, reviewed correction and original-image evidence.

## Reproduce

From the repository root or extracted experiment ZIP, with Python 3 and no packages:

```text
python experiments/records/transcription-correction-sensitivity/run.py --check
python experiments/records/transcription-correction-sensitivity/check.py
```

The first command recomputes every page and the complete LP2 corpus, then compares `results.json` and the SVG. The second independently reconstructs the reviewed strings and scans rune tokens with a separate parser. `run.py` without flags prints a compact summary. The full machine-readable result includes per-page histograms, correction fields, hashes and the exact IoC pair counts.

The next variants should test a *specified* punctuation-sensitive key clock or tokenization policy, then add newly image-reviewed disputed marks one at a time. Retain this archived-versus-reviewed baseline so any changed conclusion can be attributed to the exact edit that caused it.
