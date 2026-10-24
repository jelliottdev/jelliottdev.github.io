**None of the 26 measurements crossed the fixed threshold.** Combining next-rune prediction, compression and rune-balance measurements, 35 of 1,000 repeat-suppressed random controls scored at least as strongly as the manuscript. The predeclared 1% gate was not passed.

Two prediction orders beat a uniform guess by very small amounts. Their gains were not unusual enough under the controls: 97 controls did at least as well as KT order 4, and 27 did at least as well as order 5. These results do not establish a useful predictor or identify a cipher.

![Prediction results and control limitations](experiments/records/heldout-rune-prediction/predictive-controls.svg)

## What was measured

The test uses the same pinned source transcription as the [earlier entropy and MDL test](#/experiments/dukotah-mdl-order-profile): 55 source segments containing 12,956 rune indices. Segment ordinals differ from physical page numbers after the empty page. Even and odd source segments form two fixed training and test groups.

Each model learns from one fold and predicts runes in the other. Contexts reset at each segment boundary, and test runes never update training counts. All orders score the same 12,516 positions after the first eight runes of each segment.

The grid contains eight fixed-order KT models and eight PPM-C context models with maximum orders 1–8. KT smooths each next-rune count by one half; PPM-C escapes to shorter contexts when necessary, excluding already tried symbols. The exact escape and closed-alphabet rules are fixed in the [methods](experiments/records/heldout-rune-prediction/reproduction/METHODS.md).

Two LZMA measurements compress the whole stream: one index per byte, and source base-29 packing. These are compression measurements, **not held-out model likelihoods**. Five rolling-window measurements test unusually balanced symbol counts; three test changes in symbol frequencies across the book. They do not identify a human, deck or machine generator.

All 26 measurements use the same 1,000 seeded filtered-uniform controls. The source filter resamples a repeated rune at most once, with probability 0.83, continuously across segment boundaries. It matches repeat scarcity and uniform frequencies in expectation, rather than forcing exactly 86 repeats or exact symbol counts. The combined comparison accounts for selection across the fixed grid.

## Prediction and compression results

An uninformed uniform guess costs about 4.857981 bits per rune. Lower prediction loss is better; gain is uniform cost minus model loss.

| Predictor | Bits per rune | Gain over uniform | Controls at least as good |
|---|---:|---:|---:|
| KT order 4 | 4.857875 | 0.000106 | 97/1,000 |
| KT order 5 | 4.857774 | 0.000207 | 27/1,000 |

KT orders 6–8 are numerically equivalent to uniform within the frozen tolerance. The other eleven predictors are worse. A score below the filtered-control band would not automatically mean better prediction than uniform: unseen contexts can reduce count overfitting. Raw gains and all sixteen losses are saved, including this distinction.

Neither LZMA view crossed its comparison threshold. The packed view needs particular caution: **it flagged none of the 18 synthetic examples, including all twelve deliberately strong patterns, and produced the same 7,928-byte size for all 1,000 controls**. The eighteen examples also include deliberately permuted and mismatched-rule diagnostics. An ordinary packed-compression score cannot support an exclusion.

## Controls, checks and limits

Before target scoring, an independent implementation checked context counts, individual prediction losses, probability normalization, frozen training counts and boundary handling. Synthetic examples with first-order or second-order dependence, balanced bags and frequency drift were all detected by the combined screen: twelve deliberately strong examples across four constructions and three seeds. Permuting the second-order examples removed their flags. A deliberately mismatched training and test rule exposed transfer failures; other measurements could still detect real compression or balance in those examples. Every outcome is retained, rather than treating one easy example as validation of every measurement.

Against the final reference bank, one of 99 separate filtered-random validation streams crossed the joint gate. These decisions share a reference bank. They are a finite calibration check, not a universal false-positive guarantee.

The independent final audit reconstructed all sixteen target predictors, all 880 segment/model loss cells, both LZMA views, all eight provenance measurements, the combined rank and uniform gains. Saved reference measurements, seeds, stream hashes, folds and controls are downloadable. The exact transcription remains external; [reproduction instructions](experiments/records/heldout-rune-prediction/PORTABILITY.md) provide quick checks, independent target verification and a full temporary-output replay.

This implements selected finite versions of the public higher-order proposal. It does not test every context model, adaptive rule, cross-segment dependency or optional transformer. LZMA here is not cross-validated prediction. Neither an ordinary score nor the failed packed-compression controls establish randomness, an OTP, an absence of plaintext, or exclusion of a cipher family.
