# Two known Vigenère keys against known openings

## Why this test?

Reusing a key that already worked elsewhere is an understandable first attempt. The known Welcome and second-koan readings supply two concrete key vectors. This experiment asks whether uninterrupted use of either vector recovers any of nine recorded openings at the beginning of an archived LP2-00–55 page.

It is an exact-opening search, not a general language test. There is no reason every valid plaintext must reuse one of these openings. A negative result therefore rules out only the declared combinations and criterion.

## Plan fixed before running

The plan and runner were committed as `8a93183` before execution. The selected input is the complete archived rune stream for each of LP2-00–55, including headings. Non-alphabet characters are removed. There are no corrections, reversals, interruptions or cross-page carry.

The two key vectors are copied from the published reading parameters, without re-encoding their labels as prime values:

| Known reading | Key indices | Phases |
| --- | --- | --- |
| Welcome | 23, 10, 1, 10, 9, 10, 16, 26 | 0–7 |
| Second koan | 0, 10, 4, 0, 1, 19, 0, 18, 4, 18, 9, 0, 18 | 0–12 |

For each phase, both subtraction and addition are tested modulo 29. Each page starts independently at the selected phase. Every rune consumes one key value; punctuation consumes none. The known interruption lists are not transplanted onto unrelated pages, and there is no rule to skip every F.

This makes 42 parameter cases per page, or 2352 across 56 pages. These are parameter cases, not a claim that every output string is unique.

## Exact comparison

Each output's first 12 rune indices are compared with the first 12 indices from nine known-reading traces: Warning, Welcome, Some Wisdom, first koan, Loss of Divinity, second koan, Instruction, LP2-56 and LP2-57. The vectors, trace paths and hashes are fixed in the plan. Comparing rune indices avoids ambiguity from multi-letter Latin labels.

Each of the 2352 candidates receives nine exact comparisons: 21,168 in total. Nothing is searched at later positions. The criterion does not ask whether a candidate resembles English, has familiar short fragments, or scores well under a language model.

## Results

All 2352 cases completed, and no candidate matched any of the nine specified opening vectors. Every complete candidate sequence is retained, including its page, key ID, phase, arithmetic sign, and list of matching opening IDs. The list is empty for every case in this run.

This is not evidence that repeating keys cannot work on these pages. Different keys, interruption schedules, headings, beginnings, or page boundaries remain outside the test. It does not estimate a probability that any cipher hypothesis is true.

## Controls and independent check

The 17 known page readings reproduced before the search. Those controls use their own recorded boundary and interruption conventions; they are not counted among the 2352 unknown-page candidates.

The new decoder also recovers the first 12 known output indices of both Welcome and the second koan at phase zero with subtraction. Neither control has an interruption in those first 12 positions. This checks the same uninterrupted operation used in the new search.

A separate checker verifies every candidate using a rotated key iterator and explicit wraparound arithmetic, checks all nine opening vectors against the trace CSVs, and checks that every parameter tuple occurs exactly once. The complete runner was then repeated and every saved candidate and match decision agreed.

## Reproduce

Use Python 3.12.10 and a repository checkout. No third-party package, network connection or AI service is used.

```
python experiments/records/lp2-known-vigenere-keys/run.py --check
python experiments/records/lp2-known-vigenere-keys/check.py
```

To save a separate report:

```
python experiments/records/lp2-known-vigenere-keys/run.py --output my-known-key-scan.json
```

The output file must not already exist. [Download the saved candidates](experiments/records/lp2-known-vigenere-keys/results.json). The `alphabet` field maps indices back to runes; `sign` is -1 for subtraction and +1 for addition. Phase is the first key slot consumed at the beginning of that page. This convention resets for every case.

## Retest and later changes

Codex performed the complete rerun and independent checker on 20 October 2026. No keys, phases, opening vectors, input rules or matching criteria changed after the first result. The checker and coverage diagram were added after the search to verify and explain the saved result. Human review remains pending.

## Related work and next variants

The [fixed-alphabet experiment](#/experiments/lp2-alphabet-warning-prefix) tests a different transformation family and a single warning prefix. Its result must not be added to this record as if the criteria were identical. The [Vigenère guide](#/wiki/vigenere) explains the known key use, and the [interruption guide](#/wiki/interruptions) explains why key alignment needs care.

A justified new key list, heading convention or interruption hypothesis needs a separately declared variant. An interruption search can grow rapidly; its bounds and stopping rule must be fixed before inspecting candidate text. Do not add exceptions merely until a fragment appears readable.
