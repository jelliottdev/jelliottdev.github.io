# Does a matching decoder recover the planted message?

**With the correct key supplied, matching the decoder to the planted rule raises median recovery from 10–33% to 98–100%.** All eight generator-and-plant pairs pass the source recovery gate across seven fixed seeds each. These are controls for a decoding tool, not candidate readings of the manuscript.

![Seven seed recoveries and medians per generator and plant rule.](experiments/records/c2-extension-generator-controls/recovery.svg)

Six pairs reject a repeated ciphertext rune by consuming two key draws. Their matching paired-skip decoder has 100% median recovery. Two further plants share the Python 2.7 generator model: one adds random free advances with probability 0.05, and one adds ten evenly placed advances. Their permissive drift decoder has 98.33% median recovery. Across all 56 matching decodes the lowest recovery is 96.25%; the SHA-256 pair includes one 99.58% result, so a 100% median is not perfect recovery in every seed.

The comparison decoder is the source's `exact_ms8` beam: it allows single-draw collision skips with a skip budget of eight. It is not rigid subtraction. The same seven plaintext windows are reused across pairs; these are not 56 independent texts. All decoders receive the correct key, use beam width 400, sign -1 and starting offset zero. The source gate requires matching-rule median recovery at least 90% and comparison-rule median recovery below 90%. All eight pairs meet both conditions.

## What is distinct here?

[Round 19 repair controls](#/experiments/round19-decoder-repair-controls) compare a larger construction-and-decoder grid. [L7 score/recovery controls](#/experiments/l7-score-recovery-controls) test the scoring instrument and four older plants. [Decoder null bars](#/experiments/round19-decoder-null-bars) refit wrong-key scores. This finite Round 24 control instead checks six paired-skip generator models plus two drift plants using their source-defined streams. It belongs to the same decoder-control question and supplies no new general cipher exclusion.

The generator labels refer to Python implementations of Bash, Perl, TeX and Python 2.7 streams, plus a SHA-256 counter. This replay does not test agreement with native language runtimes. The A5 source label mentions nonzero offsets, but its control calls the decoder with `o=0`; nonzero-offset recovery is not measured. Seven generator-axis labels yield eight tested pairs because A6 has two plants.

## Exact finite replay

The package preserves the unchanged source modules, English quadgram counts, source Self-Reliance text, compact plaintext/key/ciphertext fixtures and all 112 decoded rune paths. Fixtures are regenerated from the original source functions and text selection. A fresh replay of 112 decodes exactly reproduces every archived source score and rune-recovery value. An independent checker counts correct rune indices and recomputes path scores without the beam or source scorer. Independent rescoring allows absolute 1e-12 summation roundoff; source-output comparison remains exact. The packaged plan is retrospective, based on the frozen intake and original source settings.

## Limits

These 240-rune controls use seven source seeds, one English-derived corpus and supplied correct keys. They do not calibrate wrong-key false positives, prove a large search threshold, identify the manuscript's language or cipher, or guarantee recovery for other keys or lengths. The 113,432-key manuscript sweep and wrong-key red-team were not rerun. The exact Welsh corpus and I2 panel model required for that sweep are absent; no manuscript negative follows from passing these controls.

## Reproduce offline

From the repository root:

```text
python experiments/records/c2-extension-generator-controls/run.py
python experiments/records/c2-extension-generator-controls/check.py
python experiments/records/c2-extension-generator-controls/plot.py --check
```

`run.py` repeats all 112 source beams. `run.py --check` verifies source hashes, regenerates all 56 fixtures and checks the saved traces without repeating beams. Python 3 and its standard library are sufficient. No checkout, network or missing manuscript-sweep inputs are required. Source code is MIT licensed; see the bundled license and source manifest.
