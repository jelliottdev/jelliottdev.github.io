# Can a correct key survive skipped draws?

In a proposed key-skip cipher, a key value is consumed without producing a rune when it would create an adjacent repeat. A correct key then drifts out of alignment with the visible text. The pinned [Round 18 test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L2-filter-leak) planted a known key and plaintext to ask whether its skip-aware decoder could recover them as the text grows to LP2 length.

## Finding

![Rigid key alignment detects 70 percent of 25-rune plants but only 0.5 percent of 400-rune plants. The skip-aware beam detects all 200 plants at every tested short length and recovers over 99.9 percent of plaintext runes in three full-length plants.](experiments/records/r18-keyskip-drift-power/drift-power.svg)

With the **correct planted key**, rigid decoding crosses the source's reading threshold in just **1 of 200** tests at 400 runes. The skip-aware beam crosses it in **all 200**. At **12,956 runes**, its three planted tests recover a mean **99.97%** of plaintext rune positions; all three satisfy the source's predeclared score and 90% recovery gates. A different SHA-256-counter key scores **−7.30**, below the **−5.5** reading threshold. This shows the beam can retain a known correct key at this length *under the specified simulated filter*.

The source also simulates how far the key index drifts. Its 200 full-length plants consume a mean **374.47** extra draws; the fitted geometric calculation predicts **373.61** over 12,955 transitions. That agrees with the source simulation and the separate [draw-count probability check](#/experiments/rejection-channel-information). It is a model calculation, not a measurement of an LP2 key stream.

## What was tested

The source encodes one exact King James Bible text as Gematria Primus runes, encrypts it with a seeded SHA-256-counter key, and conditionally skips draws when a candidate output repeats the previous rune. The skip probability **0.8129** was chosen from LP2's low repeat rate. A preliminary **F0 gate** checks the faster beam against the source's reference decoder on **24** seeded cases: scores agree to better than 10⁻⁹ and every plaintext path matches. Only then does the full run measure 200 drift samples, 200 planted windows at each of six lengths, and three planted full-length decodes at each of another six lengths. The source's original grid is preserved in the [complete output](experiments/records/r18-keyskip-drift-power/source-results.json).

This is a **power test for the synthetic model**. It does not show that LP2 used key skipping, identify its key, or turn a low-scoring real-page search into a proof that all possible keys fail. The planted plaintext comes from one known English corpus, and the beam's quadgram score rewards that corpus's writing. The source's own score threshold is not a family-wide error rate for an arbitrary later search.

## Reproduce

The ZIP includes the exact [KJV input](exports/sources/gutenberg-10-kjv.txt), preserved from [Project Gutenberg](https://www.gutenberg.org/files/10/10-0.txt). The runner verifies its hash; the source-code checkout and NumPy are still required.

The [replay plan](experiments/records/r18-keyskip-drift-power/plan.json) pins revision `f08b20b`, the exact source files, the recovered KJV input hash, F0 gate receipt, and B output hash. It was frozen before our replay, after inspecting the published source, so it is a source replay specification rather than a fresh preregistration. With that source checkout at `SOURCE` and its exact `kjv.txt` available:

```text
python experiments/records/r18-keyskip-drift-power/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --check
python experiments/records/r18-keyskip-drift-power/check.py
python experiments/records/r18-keyskip-drift-power/plot.py --check
```

The runner verifies every input hash, stages the source in a temporary directory, runs F0 and B, then compares **every non-timing field** with the archived output. It does not change the source checkout's tracked result files. The separate checker recalculates the drift and window-survival formulas and verifies the declared length, beam, threshold and control gates.
