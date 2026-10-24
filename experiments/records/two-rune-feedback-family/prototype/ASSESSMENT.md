# R12-C1 k=2 family engine: controls-only assessment

The complete source family is computationally practical as one grouped extension: 56 labelled branches reduce to 48 exact-equivalence branches, with a measured projection of about 8.2 minutes for one observed plus 49 complete shuffled searches. No manuscript transcription was staged, loaded or scored.

The proposed rules were frozen before this prototype in `proposal-frozen.json` (SHA-256 `61b7f559fb099cd2e325bc614702991479f5b7c69b1233ea64029a6e4b8ae8a9`). `engine.py` and `probe.py` are hash-bound there; source files are separately pinned.

## Scope and exact overlap

- Seven source functions × plaintext/mixed history × two signs × two input directions × all 841 starting-key pairs × 55 pages = 2,590,280 labelled cases. Same source page-local scoring: remove the first two decoded runes, then expand GP labels and normalize by actual Latin quadgram count. No continuous stream or different k.
- Original `public-multihistory-feedback` already covers 89,320 diagonal-primer cases in these 56 labels. The new `two-rune-primer-extension` adds 44,660 off-diagonal cases for sum/plaintext/sign−1/forward only. Their union overlaps 133,980 labels, leaving 2,456,300 additional labelled settings. These are settings, not distinct method ideas.
- After proved aliases, full scope is 2,220,240 effective cases; prior union covers 121,220, leaving 2,099,020 additional effective cases. Wulfic seed families and the feedback census use single-lag recurrence, not this two-position function basis.

## Exact aliases

For k=2, lastdiff(x,y)=y−x and alt_sum(x,y)=x−y modulo29. Thus lastdiff at sign s with seed(a,b) equals alt_sum at sign −s with seed(−a,−b). The signed pair function tables agree for all 841 history pairs, so induction proves the full plaintext arrays agree for both history sources and either input direction. 6,728 additional synthetic decoded-array checks verify the seed mapping.

This removes the eight alt_sum labels as computation, preserving all original labels and their starting-key permutation. Twelve signed function tables × two histories × two directions = 48 effective branches. Two separate 61-symbol synthetic output-set tests found exactly these 48 classes and no further coincidences; do not promote that empirical check into a universal no-other-alias theorem. Do not assume reversal or plaintext/mixed equivalence.

For tied maxima, apply original branch/page/seed order after reconstructing the aliased score array by seed permutation. Reusing a canonical winner alone can choose the wrong labelled tied primer.

## Source parity and known-input results

All 47,096 synthetic branch/primer decoded arrays and normalized scores equal the unchanged source exactly (maximum score error zero). Pair functions use a precomputed exact 7×29×29 source truth table; Numba performs direct left-to-right feedback and sequential Latin-letter scoring without fast math. It does not substitute a new language model or extend the period-three shortcut to nonlinear functions.

The 336 plants reuse two passages × three unequal starting-key pairs × 56 labels. Reversed plants are externally reversed so the decoder sees the same known reading; they are implementation/direction controls, not new independent text evidence. Every supplied true key decodes exactly and exceeds −5.5 (336/336). Under full-grid ranking, 216/336 uniquely rank truth first; 88 have ties without a higher alternative; 32 have a strictly higher-scoring alternative. Earliest-best complete recovery is 264/336; scored-tail recovery is 304/336.

All 88 ties-only cases preserve the true scored tail under the stable selected winner; 40 change only the two excluded starting outputs. The 32 higher-alternative cases differ in the scored tail. The worst selected output differs at 13 positions overall (11 scored positions). All 60 failed forward-branch uniqueness checks are retained in `control-witnesses.json`, with actual selected text/indices, scores and mismatch positions; reverse counterparts are explicitly dependent. `audit_control_witnesses.py` checks all 60 against unchanged source functions.

This separates source-score detection from exact identification. The known true text remains in every exhaustive search and passes the absolute score bar even when another candidate wins. Do not call every tie a detector-power failure, erase the misranked texts, or turn two passages into a universal language-power guarantee.

Forward-branch results below each use six plants; reverse branches have identical control outcomes by construction.

| Function | History | Sign | Unique truth first | Selected complete | Selected scored tail | Ties only | Higher alternatives |
|---|---|---:|---:|---:|---:|---:|---:|
| sum | pt | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| sum | pt | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| sum | mix | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| sum | mix | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| gemsum | pt | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| gemsum | pt | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| gemsum | mix | -1 | 2/6 | 3/6 | 4/6 | 2/6 | 2/6 |
| gemsum | mix | +1 | 3/6 | 5/6 | 6/6 | 3/6 | 0/6 |
| xor | pt | -1 | 3/6 | 4/6 | 6/6 | 3/6 | 0/6 |
| xor | pt | +1 | 3/6 | 3/6 | 6/6 | 3/6 | 0/6 |
| xor | mix | -1 | 4/6 | 5/6 | 5/6 | 1/6 | 1/6 |
| xor | mix | +1 | 4/6 | 4/6 | 5/6 | 1/6 | 1/6 |
| prime_of_sum | pt | -1 | 0/6 | 4/6 | 6/6 | 6/6 | 0/6 |
| prime_of_sum | pt | +1 | 0/6 | 1/6 | 3/6 | 3/6 | 3/6 |
| prime_of_sum | mix | -1 | 0/6 | 4/6 | 6/6 | 6/6 | 0/6 |
| prime_of_sum | mix | +1 | 1/6 | 3/6 | 4/6 | 3/6 | 2/6 |
| prime_of_gemsum | pt | -1 | 3/6 | 5/6 | 6/6 | 3/6 | 0/6 |
| prime_of_gemsum | pt | +1 | 0/6 | 2/6 | 3/6 | 3/6 | 3/6 |
| prime_of_gemsum | mix | -1 | 0/6 | 3/6 | 5/6 | 5/6 | 1/6 |
| prime_of_gemsum | mix | +1 | 1/6 | 2/6 | 3/6 | 2/6 | 3/6 |
| lastdiff | pt | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| lastdiff | pt | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| lastdiff | mix | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| lastdiff | mix | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| alt_sum | pt | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| alt_sum | pt | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| alt_sum | mix | -1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |
| alt_sum | mix | +1 | 6/6 | 6/6 | 6/6 | 0/6 | 0/6 |

## Runtime and storage recommendation

Prototype including source parity and controls took 12.45 seconds. Warm benchmarks cover random and repeated-28 inputs of lengths64/256/1024, three repeats each. Summing each branch’s worst measured seconds/rune gives 571.7 seconds for all56labels ×50whole searches, or 493.4 seconds after proved alias reuse. These are conservative measured projections, not guaranteed bounds; compilation, model setup, copying and independent checks are additional. Future runner should emit progress and preserve checkpoints.

Keep observed effective score arrays (~17.8MB, or20.7MB with every labelled alias), the explicit alias map, per-page/per-branch/global maxima, top40 global outputs, exact model/input hashes and RNG seeds. For nulls retain49×48×55 maxima plus winning primer indices (~1.3MB in packed float64+uint16), global maximum witnesses and reproducible RNG rules. Avoid the 888MB all-null effective score cube and every-candidate plaintext. One replicate’s matrices can stay in memory and be discarded after maxima/witness checks. Raw saved maxima can use compact numeric arrays with a small metadata index; JSON need not repeat every page name/model.

Reuse the already published sum/plaintext/sign−1/forward corner only if its inputs, scoring, ordering and null RNG streams are byte/semantic-identical. Selecting its existing49seeds3301241024..3301241072 and identical page-shuffle order would allow reuse of its50score slices with explicit hash verification; do not mix a differently drawn prior null panel into the new family maximum.

## Required decision before any target work

Freeze actual whole-family RNG seeds, exact alias mapping, tie ordering, checkpoint format and the purpose of failed identification controls. Recommended scope is all56source labels with48effective branches, all failures preserved, source absolute−5.5 plus max49matched whole-family null maxima+0.5, and explicit exact-recovery versus score-detection reporting. Do not silently omit failing branches, retune the model or replace texts with easier ones. A target result would concern the fixed source score rule, not exclude autokey ciphers generally. No target run is authorized or performed in this assessment.
