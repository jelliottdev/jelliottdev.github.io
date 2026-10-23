# Feedback ciphers with fixed starting values

**None of these rules recovered any of nine known 12-rune openings at the beginning of an unsolved LP2 page.** We checked 1,856 configurations, each applied to 55 pages, for 918,720 exact comparisons. These are variations of two feedback rules, not 1,856 separate historical proposals.

The question is narrow: could these feedback rules reproduce an opening already seen in a documented reading? A different plaintext opening could still be correct. A failed crib match therefore closes this particular comparison, not the feedback-cipher family.

## The rules

Each decoded rune is its ciphertext index minus a feedback value, modulo 29. Before enough runes have been read, that value is the selected scalar primer. After the chosen lag, the feedback value comes from either an earlier ciphertext rune or an earlier decoded rune.

| Choice | Tested values |
| --- | --- |
| Feedback source | Earlier ciphertext or earlier plaintext |
| Lag | 1 through 16 runes |
| Primer | Each index 0 through 28, repeated during initialization |
| Word boundaries | Continue through the page, or restart after every hyphen and period |
| Target | Each nonempty page on LP2-00–55, starting fresh at every page |
| Acceptance | Exact equality with one of nine fixed 12-rune known-reading openings |

Slashes and line breaks are layout marks in this parser. All 12,956 archived runes are retained; number-only LP2-50 supplies no rune stream. The nine openings are pinned to their original reproduction CSVs in the [manifest](experiments/suites/feedback-opening-census/manifest.json).

The longest matching prefix is **three runes**, attained by four configurations. No English-language score or statistical significance is assigned to those fragments. The [complete result file](experiments/suites/feedback-opening-census/cases.json) lists every tested rule and a digest of its full decoded output.

## How the batch is checked

The producer encrypts a synthetic plaintext and recovers it under every configuration. A separate checker reads the structured page records, implements the recurrence independently and recomputes all case digests, opening comparisons and prefix ties. It also compares the relevant one-step results with the earlier [LP2-54 header experiment](#/experiments/lp2-54-header-feedback).

This batch does not test arbitrary primer vectors, another alphabet, adding rather than subtracting feedback, skipped symbols, unknown plaintext openings, a key layer, or cribs at later positions. Those choices belong in another explicit manifest or engine version.

## Reproduce

```text
python experiments/records/feedback-opening-census/run.py --check
python experiments/suites/feedback-opening-census/check.py
```

The scripts use Python's standard library and run without a network connection. The declared rules and pinned input files are included in the experiment ZIP.
