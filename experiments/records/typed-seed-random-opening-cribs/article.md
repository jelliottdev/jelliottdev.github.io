# Typed seeds and Python Random streams

**Finding.** A published seed sweep tries words, byte strings, integers and dates as Python `random.Random` seeds. We generated its **15,408 seed–stream–sign configurations** and checked four source-defined F-rune interrupter choices for each. Across **55 nonempty LP2-00–55 page starts** and nine fixed, 12-rune known-reading openings, **none reaches 12 runes**. The longest match is five.

![The typed-seed candidates rapidly thin from first-rune matches to no complete 12-rune opening.](experiments/records/typed-seed-random-opening-cribs/typed-seed-opening-funnel.svg)

## The bounded question

The [pinned source program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/seed_sweep/string_seeds.py) specifies **1,284 typed seed values**: 68 words as strings and as bytes, 1,145 integers including the source's date grid, and three floats. Each feeds six Python Random output modes: `randrange`, `randint`, `random`, `choice`, `shuffle`, and five-bit `getrandbits`. The source tests two decode signs, making 15,408 configurations. Its decoder also tries four masks: keep or remove each of the first two F runes before the key advances.

We held the nine published 12-rune reading openings fixed and tested each against the first 12 output runes of every included page under those same interrupter choices. We used the shared exact-prefix checker with **no key skips**; the F-mask operation is the source rule here. This is a new fixed-opening test across pages, distinct from the source's original English-score test on LP2-00. It also differs from the site's separate seven-generator public PRNG sweep.

| Longest opening prefix | Mask paths |
| --- | ---: |
| 1 rune | 39,208 |
| 2 runes | 21,388 |
| 3 runes | 1,000 |
| 4 runes | 30 |
| 5 runes | 6 |
| 12 runes | **0** |

Four mask paths per configuration give **61,632 paths**. Many paths and several Python Random output modes can coincide; those paths are not independent discoveries. The test excludes these *specific* source streams as producers of the *nine chosen openings* at the *included page starts*. It does not assume the unsolved pages must begin with those readings, and it does not rule out other seeds, plaintexts, offsets or interruption rules.

## Repeat it

```bash
python experiments/records/typed-seed-random-opening-cribs/run.py
python experiments/records/typed-seed-random-opening-cribs/check.py
python experiments/records/typed-seed-random-opening-cribs/plot.py --check
```

The runner executes only the seed literals, date loop and stream function extracted from the pinned MIT-licensed source file; it does not need the source's unavailable English-scoring model. `check.py` reconciles the source's 15,408-configuration count, compares each stream mode with an independently written Python Random sample, and verifies plaintext reconstruction under all four F masks and both signs. Python **3.12** seed behavior is part of this result; the copied source code does not execute a Python 2 string-seeding implementation.
