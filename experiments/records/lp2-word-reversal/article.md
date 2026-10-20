# Reversing runes within word-like segments

A natural first idea is to read each word backwards while keeping the words in their original order. On an unsolved page, however, the archive gives us separators and line markers—not independently established plaintext words. This experiment makes that distinction explicit.

It tests two precise interpretations of the archived boundaries on LP2-00–55. All 110 cases completed and produced 110 distinct full page outputs. None matched any of the nine declared 12-rune openings. LP2-50 contains no recognized runes and contributes no candidates.

## What counts as a segment?

Both conventions include headings, preserve segment order, and reverse rune positions inside each segment. Neither changes the rune alphabet.

| Convention | Rule | Consequence |
| --- | --- | --- |
| Split lines | Every non-rune ends the current segment. | A slash or newline ends a segment even without a word separator. |
| Join lines | Remove slash, carriage return and newline before finding maximal rune segments. Every other non-rune still ends a segment. | Runes across a line boundary join unless another delimiter intervenes. |

Hyphens and periods remain boundaries under both conventions. Spaces and other non-rune characters also remain boundaries. No inference about the author's intended word division is made.

In this invented example, letters stand for single rune symbols:

```text
Input: AB/C-D
       EF.

Split lines: BA | C | D | FE  -> BACDFE
Join lines:  CBA | FED       -> CBAFED
```

The slash and newline are archive boundaries. The vertical bars in the output explanation show the segments; they are not additional input characters. A hyphen before a line break would still prevent joining.

## Difference from the row and column experiment

The [row and column baseline](#/experiments/lp2-row-column-routes) traverses rows or ordinal columns as whole groups. Here the groups are maximal rune segments under one of the two boundary rules. This is a separate experiment in the same reading-route family.

More than one scope field changes: the grouping representation, traversal procedure, number of configurations and exclusions. The comparison is not an attempt to isolate one numerical parameter. The family comparison lists these differences explicitly.

Whole-page reversal, reversing the order of words, alphabet substitution after reversal, and arbitrarily regrouping runes are not tested here.

## Inspect a real source trace

![The first six LP2-31 output positions where splitting and joining lines produce different source-position traces.](experiments/records/lp2-word-reversal/boundary-trace.svg)

The diagram reads positions from the saved result. Each number identifies a rune in the original page stream, counted from zero. The full report also retains zero-based Unicode character offsets into the exact UTF-8-decoded source file. Character offsets are not byte offsets: a rune occupies more than one UTF-8 byte.

Both permutations use every source rune exactly once. Consequently, they preserve rune counts, whole-stream IoC and single-rune entropy. Those measurements cannot choose between these two outputs; see [cipher invariants](#/wiki/cipher-invariants).

## What the result establishes

| Quantity | Recorded result |
| --- | --- |
| Declared pages | 56, including the zero-rune LP2-50 |
| Nonempty pages | 55 |
| Boundary conventions per nonempty page | 2 |
| Candidate configurations | 110 |
| Distinct full page outputs, counted within page | 110 |
| Exact opening comparisons | 990 |
| Matching cases | 0 |

The nine reference beginnings are Warning, Welcome, Some Wisdom, the first koan, Loss of Divinity, the second koan, Instruction, LP2-56 and LP2-57. The plan stores the exact first twelve decoded rune indices and the hashes of their source traces.

This result excludes only those beginnings under the stated rules. A genuine reading beginning differently would fail this test. No general English score, later-position search or statistical significance calculation was used. The [candidate-reading guide](#/wiki/candidate-readings) explains why a failed opening test is not a general rejection of a cipher idea.

## Controls and retest

The plan and runner were committed as `9b081f6` before the full page search. Neither the boundary conventions nor the acceptance rule changed after inspecting outputs.

The runner groups positions with a character-by-character scan. The checker independently locates segments with regular expressions after the declared normalization, then calculates reflected source positions for every segment. It compares every saved permutation, output and match decision, checks source hashes and opening vectors, and verifies the complete case set. The small example above also checks the production segmenter directly.

A complete second execution reproduces the saved result. This is computational review by Codex; human review remains pending.

## Reproduce and inspect

From the repository root with Python 3:

```sh
python experiments/records/lp2-word-reversal/run.py --check
python experiments/records/lp2-word-reversal/check.py
```

Save a fresh full result without overwriting the reviewed file:

```sh
python experiments/records/lp2-word-reversal/run.py --output word-reversal-rerun.json
```

The destination must not already exist. All commands use the standard library and local files. Each page has a `cases` array containing the boundary convention, segment lengths, source ordinals, character offsets, complete output indices and any matching opening IDs.

To regenerate the diagram:

```sh
python experiments/records/lp2-word-reversal/plot.py
```

## Useful follow-ups

A proposal to reverse word order, omit headings or add a substitution is a new scope. Specify its boundaries and acceptance rule before inspecting results, and retain the full traces. A broader language-ranking test needs a declared corpus, scoring rule and evaluation procedure; it should not silently replace this record's fixed-opening criterion.
