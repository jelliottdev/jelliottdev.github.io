# A rotating-key search stopped at its first screen

The [original program](https://github.com/relikd/LiberPrayground/blob/719380ebee0523ad7f2fbf389c6f960d51bea5a4/probability.py) proposes a key whose column order rotates as the text advances. It tests key lengths 3–18, rotation steps 1 through length minus one, and every starting position. On each of nine LP2 section files it first looks for the repeat-frequency band **1.6–2.1**; only settings in that band proceed to key fitting.

The published script actually passes a number where its grouping function expects a generator, so it raises `TypeError` on its first section. We tested an **explicitly repaired variant**: supply the source's own `shift_pattern(length, step)` generator at that call. We preserved its input files, first-970-symbol cutoff, group assignment and screen. The source and independent schedules agree across all 1,936 settings per section.

![The planted known text crosses the source gate, but neither the LP2 settings nor the shuffles do](experiments/records/relikd-rotated-key-source-gate/gate.svg)

On a constructed **970-rune known reading**, the declared seven-column rotating key recovered all 970 runes. Its repeat score was 1.73, and it was the only setting reported by the full 1,936-setting source grid. The plant is longer than every actual section prefix (308–796 runes). It demonstrates the mechanics on a clean example, not matched-length detection power for these sections or other plaintexts and interruptions.

Across the nine source LP2 sections, **none of 17,424 settings** reached the source's 1.6 lower gate. The highest was **1.30**, so no LP2 key was fitted and no proposed reading emerged. Forty-nine shared full-grid shuffles also produced no gated settings; their highest repeat score was 1.48. Zero source reports in both target and controls is a bounded screen result, not evidence that LP2 cannot use rotating keys. A different plaintext distribution, generator, punctuation clock or ciphertext layer could fall outside this source band.

The nine committed source rune streams match the site's LP2 rune arrays in full. For the actual search, we retain the source's punctuation and take its first 970 non-newline symbols **before** removing non-runes. This yields between 308 and 796 runes per section. Only **33 pages contributed runes**: 26 in full and seven in part. The other 22 nonempty pages were verified against the source but did not enter the search; LP2-50 is empty. The [prefix coverage receipt](experiments/records/relikd-rotated-key-source-gate/prefix-coverage.json) identifies every contributing page and the last used line and rune of each partial page. The nine source files, not hand-selected page fragments, define the test.

## Inspect and reproduce

The [control plan](experiments/records/relikd-rotated-key-source-gate/control-plan.json) and [target plan](experiments/records/relikd-rotated-key-source-gate/target-plan.json) fix the repair, scope and 49 shared shuffles. [Control results](experiments/records/relikd-rotated-key-source-gate/control-results.json), [section results](experiments/records/relikd-rotated-key-source-gate/results.json) and [null results](experiments/records/relikd-rotated-key-source-gate/null-results.json) retain the corresponding outcomes. The [separate coordinate check](experiments/records/relikd-rotated-key-source-gate/ioc-diagnostic.json) reports each section's maximum and is marked as post-result description.

With a separate checkout of the pinned LiberPrayground revision, run:

```text
python -X utf8 experiments/records/relikd-rotated-key-source-gate/source_parity.py --source-root PATH_TO_LIBERPRAYGROUND
python experiments/records/relikd-rotated-key-source-gate/source_control.py --source-root PATH_TO_LIBERPRAYGROUND --check
python experiments/records/relikd-rotated-key-source-gate/run.py --source-root PATH_TO_LIBERPRAYGROUND --workers 4 --check
python experiments/records/relikd-rotated-key-source-gate/check.py --source-root PATH_TO_LIBERPRAYGROUND --workers 4
python experiments/records/relikd-rotated-key-source-gate/coverage.py --source-root PATH_TO_LIBERPRAYGROUND --check
```

The source is read from hash-checked Git objects. Its repository has no license file, so this record does not redistribute the source code. The original script's error, the repaired program's output and the independent check are kept distinct.
