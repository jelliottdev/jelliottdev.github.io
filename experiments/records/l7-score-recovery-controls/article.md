# Can one score cutoff judge every decode?

## Finding

**A convincing score can hide an incorrect decode.** In these 28 known-key controls, four decodes passed the source's English-score cutoff while recovering less than 90% of the text we put in. The key was correct; the decoder's assumptions were not always right.

![Median rune recovery for four synthetic encryption rules; 4 of 28 controls passed the score cutoff while recovering less than 90% of the planted text.](experiments/records/l7-score-recovery-controls/score-recovery.svg)

A score measures resemblance to the model's English. Recovery measures whether the output actually matches the known text. Check both when testing a solving tool.

## Why check recovery?

The original key-skipping rule recovered every rune in all seven baseline plants. When rejecting a repeated output consumed two key draws instead of one, median recovery fell to 25.8%. Extra key advances produced intermediate results: a single extra advance gave 95% median recovery; a 2% chance of an extra advance gave 72.1%.

These are synthetic controls, not proposed readings of LP2. [Decoder repair controls](#/experiments/round19-decoder-repair-controls) already examine paired skips and drift across a larger set of constructions. This record replays four original L7 cases and combines them with its scorer and length/beam checks; it does not introduce another solving-method family.

## Different text, the same cutoff

The same correct-key trial was run three times for each of five text registers: KJV English, LP1 English, Latin, Old English and German. The Latin and Old English medians passed the −5.5 line; German's median fell just below it. That is a property of these texts, transformations and short trials—not a ranking of possible LP2 languages.

![Five registers use identical marks to compare their median correct-key scores with the fixed minus 5.5 cutoff.](experiments/records/l7-score-recovery-controls/register-scores.svg)

The original modern-English/Mabinogion and Welsh inputs were missing, so their results and the derived vowel-deletion panels are excluded. [Matched-language scorer controls](#/experiments/english-scorer-controls) compare eight languages using aligned corpus material; this smaller replay instead preserves the original L7 trial settings and the available source texts.

## Changing the decoder setting

For each of three length/beam settings, 120 controls shuffled the same source ciphertext prefix while preserving its rune counts. The score ranges changed with the setting. Each setting therefore needs a matched control; one cutoff cannot acquire a measured error rate merely by being reused.

![Observed score ranges and means for 120 shuffled controls at each of three length and beam-width settings.](experiments/records/l7-score-recovery-controls/conditional-nulls.svg)

The source's tail-scale calculation gives about **0.352, 0.135 and 0.061**, compared with its fixed default of 0.0725. Each estimate uses only **11 values above the 90th-percentile cutoff**. These are exploratory measurements, not a calibrated threshold for millions or billions of guesses. [Decoder-specific null bars](#/experiments/round19-decoder-null-bars) separately examine changes to the decoder's transition rules.

## Scope

There are 15 paired correct/wrong-key register trials, 28 mechanism plants and 360 shuffled null decodes. The original scorer, alphabet and beam modules are preserved unchanged. Compact fixtures preserve the actual rune sequences and keys used, so reproduction does not need the missing books or the larger source checkout. This package tests the saved controls; it does not re-create the entire original corpus selection.

The counts and parameters were fixed in the batch scripts before execution. The packaged plan was compiled afterward, so this is not an independent prospective preregistration. No real LP2 candidate key was searched, and no encryption method or plaintext language is ruled out.

## Reproduce

From the repository root or the extracted experiment folder:

```text
python experiments/records/l7-score-recovery-controls/run.py --check
python experiments/records/l7-score-recovery-controls/check.py
python experiments/records/l7-score-recovery-controls/plot.py --check
```

The first command repeats the source beam. The independent checker calculates rune recovery and English scores directly from the saved traces, then checks the null summaries. It does not reuse the beam to verify those calculations. The three figure files are generated from the same results.

## Sources

- [Pinned L7 source investigation](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L7-redteam/RESULTS.md).
- [Original conditional-null calculation](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L7-redteam/c1_bars.py).
