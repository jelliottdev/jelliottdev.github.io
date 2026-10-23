## Finding

**The revised scorer raises all five known-reading scores, but its wrong-key scores do not become less variable in this test.** We replayed the pinned comparison using the same five solved pages and 200 seeded random-key decodes of *A Koan*. The revised model's weakest solved-page score rose from **−4.979 to −4.774**; both clear the source's **−5.5** recognition bar. The wrong-key score standard deviation changed from **0.0880 to 0.0895**, so the source's predeclared “less variable noise” gate fails.

![Five known readings score higher under the revised model, while the observed wrong-key score spread widens slightly.](experiments/records/rune-matched-scorer-calibration/scorer-comparison.svg)

The separation between the weakest known reading and the wrong-key mean changes from **28.69 to 29.71 standard deviations**, about **3.6%**. That is a real improvement *in this particular comparison*, but much smaller than the earlier proposed **18%**. The source's saved JSON contains one narrative note saying “+2.9%”; its own tabulated values calculate to **3.6%**, consistent with its report and our replay.

## What the model actually changes

The original English quadgram table contains **7,266,795** counted windows. The revised table has the same total and **68,083** distinct four-character windows. Our independent reconstruction exactly matches its scores by making only these substitutions inside each original four-letter window: **K and Q → C, V → U, Z → S**, then combining counts for windows that become identical.

The source describes the model as handling multi-character rune transliterations such as `TH`, `EO` and `NG`. Its implementation processes the four original Latin letters individually, and every resulting window remains four characters long. Thus the measured improvement is **an alias-collapse result**, not evidence that extra rune-unit expansion improved scoring. This does not invalidate the measured scores; it makes the operation precise enough to compare with a genuinely rune-unit-aware model later.

## How we checked it

The bundled source script recovered the same five scored texts and generated the same **200** null decodes with seed **42**. It reproduced every saved page score, null summary and gate result. A separate checker rebuilt both quadgram tables, parsed the *A Koan* runes independently from the pinned transcription, reran the random keys and rescored all **205** texts without importing the source scorer.

This is a calibration of an English-language scoring instrument, **not a test of an unsolved-page cipher**. The null comes from one page and one set of 200 keys. A 0.0015 difference in the two sampled standard deviations does not establish that the revised model is generally noisier; it does mean this test did **not demonstrate the promised tightening**. Other languages and scoring registers need their own calibrated controls.

## Reproduce

From the repository root, using Python 3:

```text
python experiments/records/rune-matched-scorer-calibration/run.py
python experiments/records/rune-matched-scorer-calibration/check.py
python experiments/records/rune-matched-scorer-calibration/plot.py
```

The [measured data](experiments/records/rune-matched-scorer-calibration/results.json), [five scored texts](experiments/records/rune-matched-scorer-calibration/solved_texts.json), original executable, manuscript transcription and quadgram table are bundled from the pinned MIT-licensed source.
