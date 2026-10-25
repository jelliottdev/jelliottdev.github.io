## What the earlier results already settle

These four prepared tests ask whether a fixed rule produces the first **24 runes of the Warning reading** at the start of an LP2 page. Saved results already contain an incorrect rune before any new rule could repair it. None of these exact opening claims needs another full manuscript decode.

| Rule | First wrong rune |
| --- | --- |
| Reverse each word, then Atbash | Rune 1 on every page |
| Reverse each line, then Atbash | Rune 1; LP2-31 fails at rune 3 |
| Cumulative rule with word resets | Rune 1; LP2-01 and 54 fail at rune 2 |
| Cumulative rule with line resets | Rune 1; LP2-01 and 54 fail at rune 2 |

The table covers **55 rune-bearing pages**, LP2-00–49 and LP2-51–55. LP2-50 has no runes and is not a failed opening test. The four rows concern the same pages and related operations; they are not 220 independent scientific trials.

## Why a short mismatch settles a longer opening

An exact opening must agree at every position. If rune one or three is already wrong, computing another 21 runes cannot turn that prefix into a match. This excludes the specified opening under the specified rule. It does not exclude other plaintexts, different rules or an entire cipher family.

### Reversal followed by Atbash

The earlier [line-route experiment](#/experiments/lp2-row-column-routes) and [word-reversal experiment](#/experiments/lp2-word-reversal) saved output indices and their source positions. This audit selects the exact route used by each prepared recipe. For words, it selects the rule in which every non-rune ends a segment; for lines, it selects original line order with the runes inside each line reversed.

Atbash maps an index `x` to `28 − x` modulo 29. The Warning opening begins **24, 7, 24**. Its required input before Atbash therefore begins **4, 21, 4**. Compare this required input with the saved reversal prefixes. Every word-reversal prefix fails at its first rune. Every line-reversal prefix also fails at its first rune except LP2-31, whose saved prefix is **4, 21, 9**: its third rune is wrong. The audit checks the retained source positions against the pinned raw text; it does not decode complete Atbash target outputs.

### Cumulative decoding with resets

The specified cumulative rule is `P[k] = C[k] − sum(P[0] … P[k−1])` modulo 29, with initial sum zero and the declared reset policy. Within an uninterrupted segment this is equivalent to first differencing: the first output is the first ciphertext rune; later outputs are `C[k] − C[k−1]` modulo 29.

The [feedback-opening census](#/experiments/feedback-opening-census) already saved the exact Warning-prefix agreement bounds for that first-difference rule. Its word-reset baseline restarts at **hyphens and periods**; the prepared word recipe restarts at **every non-rune**. The saved continuous baseline ignores separators; the prepared line recipe restarts at **CR or LF**. These are different policies, so the audit locates the first position at which each new policy could change a saved output.

On 53 pages the first rune is already wrong; a later reset cannot affect it. LP2-01 and LP2-54 start with Warning's first rune, but the saved census proves that the second rune disagrees. Those disagreements occur strictly before the first differing reset under both prepared policies. Consequently the saved mismatch remains valid on all 55 pages. A mismatch **at** or **after** the changed reset would not justify this conclusion; the synthetic counterexamples check that distinction.

## What this leaves open

These are four narrow exclusions of one fixed **24-rune, page-start Warning opening**, using raw text, retained headings and the canonical 29-rune alphabet. The audit does not evaluate general readability, other openings, later start positions, corrected transcriptions, extra keys or other reset conventions. It does not show that any broader method is impossible. Re-running the prepared recipes can reproduce these exclusions, but does not constitute a new scope.

## Evidence and independent checks

The frozen plan pins source text, alphabet, Warning reading trace, saved reports and exact prepared recipe identities. Each page has a retained mismatch witness with source offsets. No complete new target output is decoded. The producer checks known-answer inverse-Atbash cases and reset-boundary counterexamples before inspecting the saved manuscript evidence. A separate checker uses independent equations and source-position checks rather than importing the producer's proof helper.

The [machine-readable report](experiments/records/prepared-opening-evidence-gates/results.json) keeps all four sets of 55 page witnesses. The [plan](experiments/records/prepared-opening-evidence-gates/plan.json) states the exact inputs and exclusions. This is a retrospective audit of saved evidence, not a prospective chance test or a newly discovered decoding.

## Reproduce

From the repository or extracted bundle root, run:

```text
python experiments/records/prepared-opening-evidence-gates/run.py --check
python experiments/records/prepared-opening-evidence-gates/check.py
```

Both use Python's standard library and pinned local files. The first rebuilds the evidence report; the second independently verifies the source links, mismatch witnesses and strict reset conditions.
