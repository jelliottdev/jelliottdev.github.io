None of the 21 fixed artifact and mathematical streams passes this source's final score gate in the declared LP2 grid. The run completes 23,100 short screens and follows 194 settings through complete-page decoding. The best returned complete score is -6.3765935, below the strict -5.5 gate. This is a measurement of a specific two-stage search, not an exclusion of numeric keys or a plaintext verdict.

## What was tested

Each page starts its key again at one of offsets 0 through 4. Both signs and ciphertext Atbash are tested. A conditional skip may reject up to three key values before accepting the next value, but each rejection must reproduce the previous transformed ciphertext rune. F is an ordinary rune; there is no F-null clock. The first min(50, page length) runes use a width-60 beam. Only scores strictly above -6.5 receive full-page width-300 decoding. The word full in the source command means all 55 nonempty pages; it does not mean full decoding of rejected screens.

## The 21 keys

This is numeric2_skip.py Part A only, pinned to Dukotah/cicada3301 commit f08b20b632d91209ddbaa747e8e2f23df0c78ba1. Its 21 arrays contain exactly 1,172 values. They include AN END bytes, reversed bytes and hex digits; the payload's hex digits; the Mayan key and reverse; three P.S. digit variants; three magic-square variants; tiled primes through 109; three 3301 variants; and Catalan, triangular, Lucas, partition and reversed-partition sequences. Reversed partition means reversal of this exact finite 1,172-value array. The source's all-offset payload and page-seeded Parts B/C are excluded.

Five key values already occur in the fixed-numeric record: forward/reverse Mayan, AN END bytes/hex digits, and the 3301 digit string. This replay adds conditional skip decoding and its bounded offsets. The magic-square row sums are all 24 modulo 29, so every offset is identical and the resulting reading is an ordinary fixed-affine transform: skipping equal key values cannot alter it. The period-four 3301 digit stream also duplicates offsets 0 and 4. Thus the 105 labeled key phases contain 100 distinct arrays within their named streams. All labeled settings are nevertheless replayed and their output aliases checked.

## Known-message controls

The reused controls establish important limits. In numeric2 PartA's 420 labeled controls, all pass both source gates but only 402 recover the exact reading. Across both numeric catalogs, 44 of 1,080 controls select a different reading. Atbash twins duplicate transformed ciphertext, leaving 22 underlying failure cases. A retrospective observer, saved before this target plan, finds that every true reading remains in the final beam at ranks 2 through 9. All selected alternatives have strictly higher cumulative scores; eight have worse normalized scores than the truth. The failure is scorer preference rather than pruning out the true reading, ties or invalid rejected-key transitions. These plants are not independent full-search false-positive calibration.

## Checking the other retained candidates

After observing the target outputs, a separately frozen POST-TARGET addendum examines all 47,782 retained terminal hypotheses across the 194 full decodes. In 164 settings another retained hypothesis has a better normalized score than the source-returned cumulative winner. None crosses -5.5; the best normalized terminal score remains -6.3765935. The historical outputs remain unchanged. This diagnostic does not search with normalized ranking at intermediate steps, recover pruned hypotheses or fully decode rejected screens.

## An example of a permitted skip

At zero-based rune position 29 on LP2-49, candidate plaintext index28 rejects key value2 because it recreates previous ciphertext index26, then accepts key value3 to give current ciphertext index25. This is an admissible candidate path, not evidence that those are the real plaintext or real skips.

## Reproduce the calculation

The bundled original source is MIT-licensed, with attribution and license retained. Reproduction uses replay.py to rerun the frozen target in a temporary copy, compare every case and all report fields except wall time, and preserve the historical outputs bound by the post-target plan. There is no global p-value, general English-recovery guarantee, OTP inference or whole-key-family negative. Other offsets, clocks, streams, languages and joined-page rules remain outside the measured scope.

The complete frozen 1,080-cell known-message controls can also be replayed offline from this extracted bundle, without a source cache. The [portable control adapter](scripts/replay_numeric_skip_controls.py) checks the original probe and used-source hashes, preserves the frozen files, and compares every skip, decoded hash, gate and exact-recovery flag; only timings are ignored, with a 2e-12 score tolerance. Run:

```text
python scripts/replay_numeric_skip_controls.py --record experiments/records/artifact-stream-skip-grid
```


## Implementation checks

The frozen target plan binds the source, quadgram model, arrays, manuscript transcription, site index and all 55 site text files before the new target calls. The source transcription agrees rune-for-rune with LP2-00 through 49 and LP2-51 through 55. The source catalog and beam functions execute unchanged inside a wrapper that records each setting; the full original driver is not executed because it also runs Parts B/C. The model scores canonical GP Latin labels. No quadgram retraining or changed source ranking is introduced. The imported sweep module also initializes a separate bigram prefilter from available texts; its missing Walden input does not affect this replay because Part A calls beam directly and never calls that prefilter. The beam uses the pinned quadgram table only.

An independent implementation reproduces all 194 returned complete-page index sequences and scores and the ten highest short outputs. It also independently rescores and checks legal key-pointer reachability for every best-normalized terminal witness, recounts all 23,100 settings and verifies phase aliases and source/site input equality. Every full output and per-setting screen hash is saved. These checks verify the recorded computation; a score-gate pass would still require independent plaintext validation.
