# Do the two preserved LP2 transcriptions change the word-length census?

**No, under Liberpedia's published rune-token rule.** The archived seventh-onion text and the wiki text have **33 different non-rune gaps across LP2-00–55**, on 24 pages. Substituting each gap into the wiki text **one at a time** changes no token-start position. Substituting the complete seventh-onion text also leaves the **2,896-token count, full length histogram, 109 tokens of length ten or more, and the one 11–11–10 window unchanged**. Both texts contain the same **12,956 ordered runes**.

![Cross-source non-rune differences by LP2 page and their token-boundary effects](experiments/records/cross-source-word-boundaries/boundary-effects.svg)

## Inputs and exact boundary rule

The [two-source transcription audit](#/wiki/seventh-onion-transcriptions) reports 36 different non-rune gaps across all **58** LP2 pages. This experiment covers the 33 on **LP2-00–55**, the corpus of the published [word-length census](#/wiki/word-lengths). The other three are on LP2-56 and 57 and are outside this comparison. The inputs are the preserved combined seventh-onion text, the 56 wiki page text files and the stored 29-rune alphabet. Every file is pinned by SHA-256 in the [plan](experiments/records/cross-source-word-boundaries/plan.json).

For each source, remove slash row markers and CR/LF wraps, concatenate pages in order, retain headings and all other characters, and match maximal rune runs with optional internal apostrophes. Count runes, not characters in their Latin labels. A token start is the zero-based ordinal of its first rune in the concatenated stream. Neither transcription is declared the correct image reading; this is a source-choice sensitivity test.

| Measure | Wiki text | Seventh-onion text |
| --- | ---: | ---: |
| Ordered runes | 12,956 | 12,956, same order |
| Rune tokens | 2,896 | 2,896 |
| One-rune tokens | 83 | 83 |
| Two-rune tokens | 448 | 448 |
| Three-rune tokens | 720 | 720 |
| Tokens of at least ten runes | 109 | 109 |
| 11–11–10 windows | 1 | 1 |
| Token starts moved | — | 0 |

The [complete result](experiments/records/cross-source-word-boundaries/results.json) lists all 33 differing gaps, their page and rune ordinal, both exact source strings, and the effect of replacing only that gap. Every one-gap variant also retains all token starts and the full histogram. This is stronger than checking aggregate counts alone: two different segmentations could accidentally have the same histogram, but here the start positions themselves agree.

## Why a visible mark can differ without changing this count

On LP2-08, a period in the seventh-onion text corresponds to a hyphen in the wiki text. Both marks separate rune runs under this tokenizer. Other differences include quotes near a rune, number-panel formatting, and terminal marks. They can be important for a rule that distinguishes a period from a hyphen, resets a key at a quote, consumes printed digits, or traverses the alphanumeric grid. This experiment does **not** test those rules. The known five grid-cell disagreements separately alter conditional base-60 bytes; the stable rune-token histogram does not settle them.

Likewise, agreement between two transcriptions does not prove that every mark on the photographed pages was copied correctly. The [page-edge sensitivity experiment](#/experiments/page-join-sensitivity) tests a different uncertainty: whether **32 rune-to-rune page edges** are joined or separated. Those edges change the token count under the same tokenizer. The present cross-source test says only that these two preserved text sources happen to make the **same** choices at every token start under this rule.

## Reproduce

From the repository root or extracted [experiment bundle](downloads/experiments/cross-source-word-boundaries.zip), with Python 3 standard library:

```text
python experiments/records/cross-source-word-boundaries/run.py --check
python experiments/records/cross-source-word-boundaries/check.py
```

The producer verifies all input hashes, reconstructs the 33 gap changes, tests each hybrid transcription, and checks the JSON and figure. The independent checker splits the combined source by page, extracts gaps and rune symbols with a separate parser, and scans token starts character by character. Neither script performs a new visual reading of the manuscript images.
