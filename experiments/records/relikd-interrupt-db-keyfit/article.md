# The saved interrupt-key candidates did not pass a known-text check

The [original LiberPrayground program](https://github.com/relikd/LiberPrayground/blob/719380ebee0523ad7f2fbf389c6f960d51bea5a4/probability.py) contains a second search path: remove selected `ᚠ` runes, fit a repeating Vigenère or affine key to the remaining text, then decode the full section while preserving the removed runes. **That path never ran in the original main loop.** A broken earlier call raises an error, and an unconditional `continue` would skip it even after that call is repaired. We extracted the saved-row operations without claiming the original program had tested them.

The source database supplies **nine candidate rows** from three sections. Each is tried with the source's two key fitters, for 18 outputs. The key fit uses only about 404–455 runes before the twenty-first `ᚠ`; it then applies the inferred key to sections as long as 3,008 runes.

![Six known-text controls are only partly recovered, although thirteen LP2 fits clear the source limit.](experiments/records/relikd-interrupt-db-keyfit/control-power.svg)

The source fitters recovered an authentic 95-rune solved page with a one-rune identity key. They also reproduced a small skipped-`ᚠ` clock example. At the saved candidates' more demanding key lengths **14, 20 and 26**, however, all six constructed known-text messages failed complete recovery. The Vigenère fits recovered 69–86% of their runes; affine recovered 35–59%. These language controls are slightly easier than the target fits because they do not delete any `ᚠ` before estimating the key.

Despite that weak control result, **13 of 18 LP2 fits clear the source's similarity limit**. This means the source limit readily reports candidate keys without demonstrating that its fitter can recover a complete known message at comparable lengths. A reported fit is **not** a reading, and the five misses do not rule out either cipher family.

The nine source rows, key lengths, skip positions, code and inputs are frozen in the [plan](experiments/records/relikd-interrupt-db-keyfit/plan.json). The [results](experiments/records/relikd-interrupt-db-keyfit/results.json) retain each fitted key, score, threshold decision and full decoded-stream hash. The source database scores that selected these rows were historical candidate metadata; we did not regenerate or broaden its interrupt search. The controls were run before these LP2 key fits. The plan records earlier exploratory known-text calibration, so its timing should not be read as independent preregistration of control choices.

To reproduce, obtain the pinned source Git revision `719380ebee0523ad7f2fbf389c6f960d51bea5a4` and substitute its path below. The scripts read and hash-check Git objects, including files omitted from a sparse checkout; they do not redistribute the unlicensed source.

```text
python -X utf8 experiments/records/relikd-interrupt-db-keyfit/run.py --source-root SOURCE --phase all --check
python -X utf8 experiments/records/relikd-interrupt-db-keyfit/check.py --source-root SOURCE
python experiments/records/relikd-interrupt-db-keyfit/plot.py --check
```
