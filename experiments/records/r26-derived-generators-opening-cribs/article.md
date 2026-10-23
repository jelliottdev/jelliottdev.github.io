# Older random generators against fixed LP2 openings

**Finding.** We rebuilt the [R26-A source grid](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round26/A/sweep.py) of Perl, TeX and Python 2.7 keystreams and asked whether any could begin an unsolved LP2 page with one of nine known 12-rune readings. Across **24,231 generated key cases**, each checked under the source's two skip rules, **none matched a complete opening**. The closest matched four runes.

![The longest opening matched four of twelve runes; no source-defined configuration matched all twelve.](experiments/records/r26-derived-generators-opening-cribs/opening-prefixes.svg)

This is a **fixed-opening check**, not a rerun of R26-A's English-scoring test. The source tested a 333-rune page with a language panel and reported an interim result. Here the question is narrower and exact: *could a named plaintext opening be structurally produced at a page start?*

## What went into the check

The source's ordered dictionary has **347 entries**: puzzle numbers, the first 200 primes, sparse dates, prime sums of solved-text words and those words as Python 2 string seeds. Its **400 integers from 0 to 399** add a small baseline. Some entries repeat values under another label. We preserved the complete executable generator grid:

| Source generator | Generated key cases | Two skip rules |
| --- | ---: | ---: |
| Eight Perl `rand` reductions | 5,696 | 11,392 |
| Four TeX random generators | 2,848 | 5,696 |
| Three Python 2.7 reductions, seven offsets each | 15,687 | 31,374 |
| **Total** | **24,231** | **48,462** |

Those cases contain **19,986 different first-100-symbol streams**; repeated seeds and equivalent settings make some duplicate prefixes. The case count describes the source grid, not 24,231 independent ideas or keys.

Perl and TeX accept integer seeds here; Python 2.7 also accepts the 35 word seeds. Python 2.7 uses the source's 64-bit seeding path and offset list **0, 1, 2, 3, 5, 7, 13**. The source's `count_decodes()` announces 49,302 rows because it counts all 347 dictionary entries for Perl and TeX. Its actual loop skips their 35 string seeds, removing **840** rows. We counted the executable loop, not the announced estimate.

For every key stream, we tested the first 12 runes on all **55 nonempty pages in LP2-00–55**—LP2-50 is blank—against the same **nine predeclared 12-rune openings** used in the site's other fixed-opening experiments. We kept the source's subtraction direction, no Atbash, and zero starting offset. The `exact` rule may reject up to three key symbols before an accepted rune; each rejected symbol must otherwise repeat the previous ciphertext rune. The `pair` rule may reject up to eight in pairs; the first symbol of each rejected pair must make that repeat. Every feasible path is considered, without an English-score beam that could prune one.

Only the first **100 key symbols** are needed to test a 12-rune opening under the larger eight-rejection bound. Generating a longer forward stream would leave those symbols unchanged. This shortens the computation without truncating any possible 12-rune path.

## Result and meaning

| Longest feasible prefix among the nine openings and 55 pages | Configurations |
| --- | ---: |
| 1 rune | 30,680 |
| 2 runes | 16,909 |
| 3 runes | 842 |
| 4 runes | 31 |
| All 12 runes | **0** |

A one-rune match says little: each key is compared with many page-and-opening pairs. The decisive fact for this specific test is that **no complete 12-rune opening is possible anywhere in the declared grid**. That does *not* show that these generators cannot encrypt LP2. The unknown pages might begin with other words, use another offset or direction, reset the key, or follow a different transition rule. The original R26-A language-panel outcome is a separate claim.

## Reproduce and inspect

From the repository root:

```bash
python experiments/records/r26-derived-generators-opening-cribs/run.py
python experiments/records/r26-derived-generators-opening-cribs/check.py
python experiments/records/r26-derived-generators-opening-cribs/plot.py --check
```

The ordered seed manifest and original generator modules are bundled with the record under the source's MIT license. The results file records each generator/preset distribution, every complete match (there were none), and a digest over all 48,462 configuration results. An independent checker regenerates the full grid with a separate path-state implementation, compares that implementation with brute tree search on 400 small cases, verifies generator vectors against independent arithmetic or a captured Python 2.7 vector, and recovers planted no-skip and forced-skip openings. Current site rune transcriptions and the published reading cribs are the target inputs; changing either requires a new run.
