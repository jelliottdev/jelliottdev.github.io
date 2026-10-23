## Finding

The published B-05 test asks whether the hidden 256-byte grid can generate a key for the unsolved runes. We replayed its remaining fixed searches: **40,320 main-grid cases**, **3,480 constant-shift cases**, and **23,040 one-byte-variant cases**. None reached the source's required English score of **−5.5**. The strongest scores by part are shown below; a higher score is better.

| Source search | Best score | Passed |
| --- | ---: | ---: |
| Main grid | −6.770531 | 0 |
| Constant shifts | −6.889604 | 0 |
| One-byte variants | −6.744875 | 0 |

![Best scores from the three source searches beside the fixed English threshold.](experiments/records/grid-payload-prf-source-grid/result-score.svg)

The [separate two-witness test](experiments/records/grid-payload-prf-contested-masks/article.md) completed the source's other **3,840** head-screen calls. Together, these records cover all **70,680 predeclared B-05 head-screen calls**, with the exact source input and scoring rule.

We also replayed the source's two follow-ups. The best of **180 rigid-decoder corners** scored **−7.096043**. The five strongest main-grid settings on the first 400 runes scored **−6.771 to −6.863** there; over the full unsolved rune stream, each fell to **−7.223 to −7.333**. Thus no head-screen survivor strengthened when given more text. The [individual follow-up scores](experiments/records/grid-payload-prf-source-grid/followup.json) are saved alongside the grid.

## How the replay avoids duplicate work

The source often reaches the same decoder input through different settings. For example, a short-key generator ignores grid bytes beyond its key length; a zero constant shift repeats an unshifted case. We retained **every original configuration and score** but decoded each distinct effective key once. There were **59,948** distinct key inputs across the 70,680 source calls; **2,596** had already been scored in the two-witness test.

This sharing is exact for the first 400 runes. With at most three key skips between runes, the source beam cannot read beyond the first **1,597** key values after its offset. Reversing, mirroring, shifting and applying the sign before comparing those values identifies identical decoder inputs. All saved two-witness scores agree within each duplicate group. We also compared the transformed-key decoder with direct source calls covering reverse keys, Atbash, both signs, offset 3301, constant shifts and one-byte variants.

The four source planted controls passed, as did [30 extended generator/reduction controls](experiments/records/grid-payload-prf-contested-masks/control-all.json). This result is limited to the source's English model, first 400 runes, listed payload readings and key operations. Its shuffled-text maximum is a reference, **not** a chance threshold adjusted for choosing the best of tens of thousands of cases; the fixed −5.5 requirement decides the recorded hits.

## Reproduce

The [complete configuration scores](experiments/records/grid-payload-prf-source-grid/cases.jsonl), [summary](experiments/records/grid-payload-prf-source-grid/results.json), and [follow-ups](experiments/records/grid-payload-prf-source-grid/followup.json) are saved. From the repository root, Python 3 with `cryptography` runs the replay. Four worker processes use an internal checkpoint outside the published site:

```text
python experiments/records/grid-payload-prf-source-grid/dedup_engine.py --run --workers 4
python experiments/records/grid-payload-prf-source-grid/check.py
python experiments/records/grid-payload-prf-source-grid/followup.py --check
```

The engine first proves parity with the completed source cases, then resumes only missing key scores. [Pinned source files](experiments/records/grid-payload-prf-seed-corner/source-manifest.json) and the MIT license are included in the reproduction bundle.
