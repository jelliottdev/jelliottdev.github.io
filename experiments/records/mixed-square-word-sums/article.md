# Candidate words for the LP1-05 mixed square

This experiment checks sixteen supplied word-and-total pairs. It asks whether each spelling can be segmented into Gematria Primus rune labels to produce the proposed number. It does not try the words as keys or replace text on unsolved pages.

## Scope and normalization

The list was fixed before enumeration. Uppercase each word and replace V with U; make no other spelling substitutions. Enumerate every exact segmentation into the 29 Latin rune labels in the archived alphabet. For example, TH can be one rune label or the two labels T and H. These are spelling segmentations, not a phonetic transcription algorithm.

There are 16 candidates and 24 total segmentations. Every candidate has exactly one segmentation matching its supplied total. Fourteen candidates have only one possible segmentation under these rules; THAN has two and AETHEREAL has eight. The candidate list was supplied because its sums were of interest, so the 16 matches are not an unbiased success rate or a chance probability.

## Matching segmentations

Each row below records the exact rune labels needed. VOID is retained as the submitted word, with V explicitly normalized to U.

| Candidate | Rune labels | Sum |
| --- | --- | --- |
| OR | O · R | 18 |
| FORM | F · O · R · M | 91 |
| VOID | U · O · I · D | 130 |
| THAN | TH · A · N | 131 |
| WHEN | W · H · E · N | 138 |
| FIND | F · I · N · D | 151 |
| BUFFERS | B · U · F · F · E · R · S | 199 |
| MOURNFUL | M · O · U · R · N · F · U · L | 199 |
| MOBIUS | M · O · B · I · U · S | 226 |
| OBSCURA | O · B · S · C · U · R · A | 245 |
| IMPOSE | I · M · P · O · S · E | 272 |
| CARNAL | C · A · R · N · A · L | 320 |
| ANALOG | A · N · A · L · O · G | 320 |
| SHADOWS | S · H · A · D · O · W · S | 341 |
| CABAL | C · A · B · A · L | 341 |
| AETHEREAL | AE · TH · E · R · EA · L | 366 |

## What the Latin spellings leave undecided

THAN gives **131** with TH–A–N, but **208** with T–H–A–N. AETHEREAL has the following eight exact-label segmentations:

| Rune labels | Sum |
| --- | --- |
| A · E · TH · E · R · E · A · L | 484 |
| A · E · TH · E · R · EA · L | 429 |
| A · E · T · H · E · R · E · A · L | 561 |
| A · E · T · H · E · R · EA · L | 506 |
| AE · TH · E · R · E · A · L | 421 |
| AE · TH · E · R · EA · L | 366 |
| AE · T · H · E · R · E · A · L | 498 |
| AE · T · H · E · R · EA · L | 443 |

When the original manuscript supplies rune symbols, use those symbols directly. The ambiguity here arises when converting a Latin candidate back into runes. Choosing the segmentation because it hits a target is a search choice and must be recorded; the Latin word alone does not fix the sum.

## Why equal totals do not recover words

The [mixed-square guide](#/wiki/magic-squares?section=sum-collisions) already shows distinct printed words sharing values: BUFFERS and MOURNFUL both give 199, CARNAL and ANALOG both give 320, and SHADOWS and CABAL both give 341. A sum discards order and other information. A number-to-word replacement can therefore have multiple candidates even in this small supplied list.

If every cell of a magic square is replaced by a word with exactly the same numerical total, all its line sums remain unchanged by construction. Preserving 1033 would check the replacements' arithmetic; it would not independently select the words or establish a hidden sentence. The [known conversion](#/wiki/magic-squares?section=rune-cells) goes from visible runes to numbers; reversing that process is a different problem.

## Reproduce

Run the producer and independent checker from the extracted experiment bundle or repository:

```text
python experiments/records/mixed-square-word-sums/run.py --check
python experiments/records/mixed-square-word-sums/check.py
```

Without `--check`, the producer prints all results as JSON. The producer recursively matches alphabet labels at the start of each remaining suffix. The independent checker instead tries every cut/no-cut pattern between Latin letters, keeps only pieces in the alphabet, and compares the complete set of segmentations and sums. Both use the same declared alphabet; agreement is not an independent verification of that alphabet against the manuscript.

The plan fixes the words and target totals. The JSON retains every segmentation, including nonmatching ones. No dictionary, language model, network access or paid service is needed.

## Limits and related experiments

This is an arithmetic audit of a selected list, not an exhaustive dictionary search, plaintext result or test of authorial intent. It does not establish that an unsolved rune word with one of these totals should be decrypted using the corresponding candidate. That would require a defined transform, alignment, key-advance rule and scoring criterion.

A future variant can change the vocabulary or transliteration rules while preserving this baseline. A dictionary search must pin the dictionary and report all matching entries, not just appealing words. A cipher search must state its [search space and bounds](#/wiki/search-space) separately. The [magic-square freedom experiment](#/experiments/magic-square-freedom) concerns numerical constraints; it answers a different question.
