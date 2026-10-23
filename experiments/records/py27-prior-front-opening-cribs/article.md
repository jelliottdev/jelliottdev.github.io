# Python 2.7 priority seeds against fixed LP2 openings

**Finding.** None of the **45,975 priority words** in the published [R21-L3 sweep](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map/sweep.py) produces any of nine fixed 12-rune known-reading openings at the start of the 55 nonempty pages in LP2-00–55. We checked all four source generator settings—**183,900 generated cases**—under the source's key-skip rule. The closest match reaches five runes.

![No Python 2.7 priority-seed case matches a complete twelve-rune opening; the longest match is five.](experiments/records/py27-prior-front-opening-cribs/prior-front-prefixes.svg)

## What was checked

The source orders 433 proposed 32-bit words, then adds the ±512 neighbourhood around its first 64 words, removing repeated values. That yields **45,975 words** before its later dense-from-zero search. We reconstructed the order from the pinned `seedprior20.json` and checked its SHA-256 digest against the earlier source audit. For each word we used exactly the source's four settings:

| Setting | How the key starts |
| --- | --- |
| `grb5_mod_i386` | One 32-bit seed word; five random bits modulo 29 |
| `grb5_rej_i386` | One 32-bit seed word; reject five-bit values 29–31 |
| `shuffle29_i386` | One 32-bit seed word; repeated shuffled rune alphabet |
| `random29_amd64` | Multiply the word by the source constant into 64 bits; seed with its low and high 32-bit words |

We generated the first **45 key symbols**, enough to allow 12 accepted symbols with up to three rejected symbols between them. A rejected symbol is permitted only if it would have repeated the preceding ciphertext rune. The test searches every valid skip path, without ranking or discarding one because its English score looks poor. It uses the source's subtraction direction, zero starting offset, no Atbash, and the same nine predeclared openings used in other site experiments.

## What the result means

| Best opening prefix per case | Generated cases |
| --- | ---: |
| 1 rune | 115,884 |
| 2 runes | 64,488 |
| 3 runes | 3,409 |
| 4 runes | 108 |
| 5 runes | 11 |
| All 12 runes | **0** |

There are **183,356 different first-45-symbol streams** among the 183,900 generated cases. The counts above are settings and seeds tested, not separate solving ideas. The useful conclusion is limited: *this priority seed grid cannot produce any of these nine exact openings at those page starts under the stated skip rule.* Other plaintext openings, later positions, further seeds and other key rules are outside the result.

R21-L3 originally screened **884,000** word-and-setting cases on LP2-00 with an English-language panel. This record does **not** reproduce that language-panel claim: its model inputs are unavailable in the pinned source. The fixed-opening criterion here is independent of that panel and asks a narrower, directly checkable question.

## Reproduce

From the repository root:

```bash
python experiments/records/py27-prior-front-opening-cribs/run.py
python experiments/records/py27-prior-front-opening-cribs/check.py
python experiments/records/py27-prior-front-opening-cribs/plot.py --check
```

The record bundles the pinned source seed list and Python 2.7 generator under their MIT license. `results.json` gives each setting's prefix counts and a digest over all 183,900 case results. The separate checker rebuilds the whole grid, uses its own exact path-state search, checks 400 small cases against brute tree search, verifies a reference MT19937 output vector, and recovers planted openings with and without a forced skipped key symbol.
