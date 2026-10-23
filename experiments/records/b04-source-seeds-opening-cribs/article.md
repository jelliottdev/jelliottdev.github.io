# Cryptographic seed streams against fixed LP2 openings

**Finding.** We generated all **1,385,600** configurations in a published cryptographic-keystream grid and checked whether any can produce one of nine fixed, 12-rune known-reading openings at the start of the **55 nonempty pages in LP2-00–55** (LP2-50 is blank). **None reaches 12 runes.** The longest structurally possible prefix is six. This checks a new, narrow question against the published key candidates; it does not reproduce the source project's original English-scoring sweep.

![Of 1,385,600 configurations, one can match six runes of a fixed opening, but none can match all twelve.](experiments/records/b04-source-seeds-opening-cribs/opening-prefix-funnel.svg)

## What we tested

The [B-04 source dictionary](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round13/B04/seeds.py) provides **2,165 distinct byte seeds**, drawn from puzzle words, numbers, addresses and other source material. The [source generator](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round13/B04/ks.py) expands each seed through 16 byte-stream generators (including hashes, HMAC, RC4, AES-CTR and ChaCha20) and five reductions to the 29-rune alphabet. We kept the source's forward/reversed stream, both decode signs, optional Atbash on the ciphertext, and zero key offset. That is **2,165 × 16 × 5 × 2 × 2 × 2** configurations.

For each configuration we asked a fixed question: could the first 12 ciphertext runes of any included page decode to the first 12 runes of any of nine published readings? The readings were fixed before this run and their source CSV hashes are in the result file. Each page starts a fresh key stream. The solver permits **zero to three rejected key symbols** between emitted runes, exactly the key-skip rule used by the [source decoder](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/campaign18_skip/skipdecode.py). A rejected symbol is allowed only if it would have repeated the preceding ciphertext rune. We checked path existence exactly, without pruning paths by English score. For the reversed-key branch, we generated the full source-length stream before reversing it.

## What happened

| Longest possible prefix | Configurations |
| --- | ---: |
| 1 rune | 890,320 |
| 2 runes | 469,639 |
| 3 runes | 24,653 |
| 4 runes | 950 |
| 5 runes | 37 |
| 6 runes | 1 |
| 12 runes | **0** |

These counts give the *best* prefix across the 55 pages and nine cribs for each configuration. A one-rune match is expected often because there are many possible page-and-crib pairs; the result that matters for this bounded claim is **zero complete 12-rune openings**. This is an exact search over the declared grid, not a statistical estimate of every possible key.

The source B-04 campaign scored candidate plaintext as English on the first 120 runes of LP2-00. Our check changes both the target and the test: it searches page starts across LP2 for **nine specific openings**. Therefore the finding should be read as: *these source-defined zero-offset keystreams do not produce those openings under this structural key-skip rule*. It does not establish that LP2 begins with one of those readings, nor that the entire keystream family has been eliminated. Other plaintexts, offsets, word resets, key-construction changes, and different transcriptions remain outside this record.

## Reproduce and inspect

The bundled seed manifest records the exact ordered source seed bytes. From the repository root, run:

```bash
python experiments/records/b04-source-seeds-opening-cribs/run.py
python experiments/records/b04-source-seeds-opening-cribs/check.py
python experiments/records/b04-source-seeds-opening-cribs/plot.py --check
```

`run.py` emits aggregate counts and a SHA-256 digest of every configuration's best prefix and full-match list; the per-configuration grid is not presented as 1.38 million separate experiments. The independent checker compares the dynamic program with exhaustive skip-path enumeration on 400 random cases and 100 constructed valid skip paths, then verifies planted no-skip and forced-skip positives. The source code copied here retains its MIT license. The experiment uses the site's current page transcription and published reading CSVs; changing those inputs requires a new run.
