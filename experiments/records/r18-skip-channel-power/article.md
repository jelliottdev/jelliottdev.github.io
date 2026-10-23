# Can inferred key skips identify a correct key?

A [Round 18 source test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L2-filter-leak) proposes counting how many key draws a skip-aware decoder uses. If a key is right, its winning path may use a different number of skips from a wrong key. We ran the pinned source's full B5 program, including the candidate-ranking loop left unfinished in its saved receipt.

## Finding

![The planted correct key has more beam-inferred skips than the 40 wrong keys on planted text. The best of 20 real candidates overlaps the 40 wrong keys on LP2.](experiments/records/r18-skip-channel-power/skip-counts.svg)

On a **synthetic text encrypted with a known key**, the decoder reports **362 skips**, one away from the planted process's actual **361**. Forty deliberately wrong keys on the same text average **296.3 skips** (range **240–348**). The true-key count is **3.08** of those samples' standard deviations above their mean. This demonstrates separation for this one planted construction.

On the real **12,956-rune LP2 stream**, forty wrong keys average **297.8 skips** (range **260–357**). The finished source run also checks **20 candidates** selected from earlier key searches. Their highest count is **353**, within the wrong-key range and **2.78** standard deviations above its mean; none reaches 3. Their English scores remain around **−7.25 to −7.32**. This bounded test gives no supported LP2 reading or key.

The source describes skip count as a second, English-independent channel. The executable decoder actually **scores plaintext quadgrams while choosing each beam path**, then counts skips on the winning path. The count is therefore affected by that English-based path choice. It is useful as a diagnostic of the decoder, but this implementation does not establish a language-independent measurement.

## What was checked

The [plan frozen before our run](experiments/records/r18-skip-channel-power/plan.json) pins the source revision, dependencies, original result, controls and search bounds. The first B4 stage exposed a missing ignored generated input; the [separate amendment](experiments/records/r18-skip-channel-power/plan-amendment.json) pins its recovered bytes. B5 was run in the same disposable staging process, without changing the source checkout. The source's saved B5 file contains both complete 40-key null samples but an incomplete candidate loop. We reproduce the saved sample statistics exactly and retain the completed 20-candidate output.

The source's stored expected-skip projection differs by **0.0077 skips** from the current pinned executable; the reason for that small difference is unverified and it does not affect the counts above. Its reported “92% screening power” comes from a fitted approximation around one planted true key, rather than repeated held-out true-key trials, so we do not treat that as an observed power estimate.

This checks one skip rule, one synthetic true key, forty specified wrong keys per stream, twenty previously selected real candidates, and an English-scored beam width of 400. Other keys, skip laws, language models and held-out texts remain outside this result. The earlier [drift-ladder test](#/experiments/r18-drift-ladder-replay) covers candidate offsets; this record covers the distinct full-stream skip-count question.

## Reproduce

Use the [pinned source revision](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1) as `SOURCE`. This complete source stage is long-running. The runner checks exact dependency hashes and stages a temporary copy; it does not overwrite the checkout:

```text
python experiments/records/r18-skip-channel-power/run.py --source-root SOURCE --kjv exports/sources/gutenberg-10-kjv.txt --stage skipchannel
python experiments/records/r18-skip-channel-power/check.py
python experiments/records/r18-skip-channel-power/plot.py --check
```

The [saved source receipt](experiments/records/r18-skip-channel-power/source-b5_skipchannel.json) and [completed replay](experiments/records/r18-skip-channel-power/replayed-b5_skipchannel.json) are available. The independent checker rebuilds the original null means, spreads, ranges and all twenty candidate standard scores without calling the beam decoder.
