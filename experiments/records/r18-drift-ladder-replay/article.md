# Does key skipping move a page's starting position?

If an encryptor discards some key draws to prevent repeated output runes, the key position at a later page is **not** simply the number of preceding runes. This [published Round 18 test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L2-filter-leak) searches a predicted band of later key positions. We replayed its planted-key control and its search over previously reported candidate keys.

## Finding

![Three planted pages score much better at the corrected key position than at the uncorrected one. In the real manuscript, neither the best corrected score nor the best overall score reaches the source's reading bar.](experiments/records/r18-drift-ladder-replay/drift-ladder.svg)

The correction matters **when the simulated key is known to be right**: on three planted pages, the true offset ranks first, scoring about −4.0. Starting at the uncorrected position scores around −7.0 to −7.3 on those same pages. The planted control therefore shows that an otherwise good key could be missed by a rigid page-start test under this particular skip model.

On the real LP2 transcription, the source tests **230 candidate keystreams** mined from its earlier top lists. Each is checked at **5,961 positions** across the first 100 runes of each of **55 nonempty pages**: **1,371,030 decodes**. The best result in the newly corrected positions is **−6.012**. The best overall, **−5.885**, is at a previously tested page-restart position. Both remain below the source's declared **−5.5** reading bar. No candidate in this bounded set supplies a supported reading.

The source numbers the nonempty text segments from zero. Its “page 52” is **LP2-53** in the manuscript: LP2-50 has no rune text and drops out of that numbering. We checked this mapping against all 56 LP2-00–55 page records.

## Scope and limits

The offset band assumes one continuous 29-value key stream, a per-draw skip probability derived from the manuscript's low adjacent-repeat rate, and a maximum of three skipped draws at a step. The source searches a predicted four-standard-deviation band plus uncorrected and page-restart controls. It inspects 100 runes per text page. The 230 keys came from earlier score-ranked lists; they are **not every possible key**. A low score here does not reject every key-skip method, other global starts, page rules, or later text.

The **−5.5** bar is the source's historical English-score gate, not a fresh held-out calibration for all choices behind this search. The plant verifies recovery under its synthetic rule, not that LP2 used that rule.

## Reproduce

The [source-read replay plan](experiments/records/r18-drift-ladder-replay/plan.json) pins the source revision, candidate-list inputs, KJV text, and original output hashes. This B4 publication scope was derived from the [combined plan frozen before our replay](experiments/records/r18-drift-ladder-replay/combined-plan-as-frozen.json); neither plan is an independent preregistration of the published method. The first isolated pass exposed one missing staged input for the PRNG candidates. The [dependency amendment](experiments/records/r18-drift-ladder-replay/plan-amendment.json) pins an archived `ct.bin` that independently matches the source's `prep.py` output. We retained the 210 completed rows and retried the 20 affected candidates. The runner checks these bytes, stages files in a temporary directory, and leaves the source checkout untouched. Use the pinned source checkout as `SOURCE`:

```text
python experiments/records/r18-drift-ladder-replay/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --stage gate
python experiments/records/r18-drift-ladder-replay/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --stage b4pc
python experiments/records/r18-drift-ladder-replay/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --stage ladder --nproc 6
python experiments/records/r18-drift-ladder-replay/check.py
python experiments/records/r18-drift-ladder-replay/plot.py --check
```

The complete [source ladder](experiments/records/r18-drift-ladder-replay/source-b4_ladder.json) and [our replay](experiments/records/r18-drift-ladder-replay/replayed-b4_ladder.json) are retained. The checker compares all **230** candidate rows independent of multiprocessing order and derives the offset count from the page records. It also verifies the source's ordinal-to-page mapping.
