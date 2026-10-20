# N-rune gaps on LP2-00–02

This experiment reconstructs a proposed extraction from distances between successive N runes. It compares four configurations: position distance or intervening-rune count, each with page resets or cross-page continuation. It does not test whether the signpost artwork instructs this operation.

## Inputs and scope

Use the archived rune-only streams from LP2-00, LP2-01 and LP2-02, including headings. Preserve rune order; discard punctuation and whitespace for the distance calculation. There are 262, 266 and 201 runes respectively, with 12, 8 and 8 occurrences of N.

The proposal and initial output were known before the plan was written. This is an exploratory reproduction, not a preregistered confirmation. No other target rune or parameter search is included.

## Two definitions of distance

If N occurs at rune positions 22 and 24, the position distance is 2, but only one rune lies between the two Ns. The first definition maps 2 to F through its Gematria Primus prime value. The second produces 1, which has no GP prime-value mapping.

For each adjacent pair of Ns, retain the exact distance and both source locations. Map a distance only when it equals one of the 29 GP prime values. Keep all other distances as a dot token. These dots mark unmatched observations; they are not manuscript punctuation. No gap is deleted or rearranged.

Page resets produce 11, 7 and 7 gaps. Joining all three streams produces 27 gaps, including the two cross-page gaps. The four configurations yield eight reported streams because reset configurations return one stream per page.

## Complete outputs

Each space separates one gap observation. Do not read spacing as recovered word boundaries.

### reset-at-page / position-distance / lp2-00

```text
F R O . M . . . . . I
```

### reset-at-page / position-distance / lp2-01

```text
. O . . . . .
```

### reset-at-page / position-distance / lp2-02

```text
. . . . . . .
```

### reset-at-page / intervening-runes / lp2-00

```text
. . . U . R . U P U .
```

### reset-at-page / intervening-runes / lp2-01

```text
. . . . X N R
```

### reset-at-page / intervening-runes / lp2-02

```text
. . I G . I .
```

### join-pages / position-distance / lp2-00, lp2-01, lp2-02

```text
F R O . M . . . . . I . . O . . . . . S . . . . . . .
```

### join-pages / intervening-runes / lp2-00, lp2-01, lp2-02

```text
. . . U . R . U P U . . . . . . X N R . . . I G . I .
```

## What the apparent fragment depends on

LP2-00 starts with position distances 2, 11, 7, 4 and 71. Their output is F, R, O, dot, M. A contiguous FROM requires discarding the unmatched distance 4. That is a different extraction rule from retaining every observation.

The joined position-distance stream adds a distance of 40 across LP2-00 to LP2-01, which stays a dot, and 53 across LP2-01 to LP2-02, which maps to S. The S therefore does not arise within LP2-02 under the page-reset rule. Every endpoint is in results.json, with one-based page-local rune ordinals and zero-based source-character offsets.

The outputs reproduce a fragment that can invite an English reading after selection. They do not provide a full reading or establish an intended cipher. No p-value is calculated: accounting for choices among target runes, distance conventions, page boundaries and output selection would require a separate search and control model.

## Reproduce and inspect

Run from the repository or the extracted experiment ZIP, retaining its folder layout:

```text
python experiments/records/n-rune-gaps/run.py --check
python experiments/records/n-rune-gaps/check.py
```

Python 3 is sufficient. The first command regenerates all outputs and compares them with the saved report. The second independently splits the rune streams at N and checks gap lengths, mappings, source locations and cross-page flags. No network or model calls are made.

The result is inconclusive about a cipher, while the extraction itself is reproducible. Human review is pending. Further tests must state any changed target, omitted heading, character representation or filtering rule; record such changes within the same experiment family rather than presenting them as confirmations of this scope.
