# Do common key-stretching recipes unlock LP2's opening?

A short password might generate a much longer numeric key. This [published screen](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/KDF/RESULTS.md) tried that possibility on the **first 120 unsolved LP2 runes**. It crossed a fixed list of puzzle-related secrets with familiar password-to-key recipes, then applied each resulting stream through a decoder that can account for skipped key symbols.

## Finding

**None of the 692,064 LP2 decodes passed the source's English-score requirement.** The best scored **−6.259**, while a candidate needed at least **−5.500** to advance. A message deliberately encrypted with one of the tested recipes *did* come back as the top result at **−4.186**. The control shows this particular search can find one of its own planted messages; it does not establish that every possible real encoding would be found.

![The planted message scores above the advancement bar; the strongest LP2 candidate stays below it.](experiments/records/public-kdf-seed-stretch/scores.svg)

These are English four-letter-pattern scores: higher values are stronger. The strongest LP2 output still does not read as an English continuation. It used the secret `sacrifice`, 100,000 rounds of iterative SHA-256, the secret itself as salt, rejection reduction to rune indices, an Atbash transform, and a reversed key stream. That is the **best measured configuration**, not evidence that any of those choices is a clue.

## What the search actually covered

The code built **534 distinct secret byte strings** from the source's puzzle phrases, solved-page words, numbers, prime sequences and other named artifacts. For each secret it tried **27 key-derivation configurations**: PBKDF2 variants, scrypt, iterated hashes and OpenSSL-style derivation. It then crossed three salts (`empty`, `3301`, and the secret itself), two byte-to-rune reductions, both arithmetic signs, Atbash on or off, and forward or reversed key output. All began at **key offset zero** and were scored against the same 120-rune LP2 prefix.

The source first ran two controls. One recovered a message from a short-seed SHA-256 expander with **98.9%** character agreement; the other planted a PBKDF2 message and searched the *entire same configuration grid* against it, ranking the planted setting first. The latter required another 692,064 control decodes. Those are a power check, not another 692,064 distinct LP2 hypotheses.

The source's 200 shuffled-text comparisons use one fixed control key. They do **not** rerun the full 692,064-choice search on each shuffle, so they do not provide a calibrated probability for the winning LP2 score after selection. The finding here is narrower and cleaner: the executed grid, with its stated English threshold, produced no advancing LP2 result.

This does not test a different secret, salt, iteration count, starting offset, language, changing key by page, or a longer portion of LP2. It says nothing about whether LP2 could use a key-stretching recipe outside this specific grid.

## Reproduce

Download the record's ZIP to inspect the pinned code and inputs. The bundled subset is byte-for-byte source code and the input files that affect this run; its rebuilt **ordered 534-secret dictionary matches the full source checkout by SHA-256**. From a Liberpedia repository checkout:

```bash
python experiments/records/public-kdf-seed-stretch/check.py
python experiments/records/public-kdf-seed-stretch/run.py
```

The checker quickly verifies the saved results, grid count, controls, source dictionary and strongest candidate. The full replay takes much longer and runs in a temporary copy, keeping archived output hashes stable. It executes the source's `K1,K2,A` stages; `--nproc 8` changes worker count, not which configurations are tested. The original K1 program prints its result but does not rewrite the JSON file that the sweep reads. Our runner therefore checks its [live output](experiments/records/public-kdf-seed-stretch/k1_control_output.txt) and exit status against that pinned file before starting the sweep.

Read the [pinned plan](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/KDF/PREREG.md), [source executable](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round15/KDF/sweep.py), [complete Stage A result](experiments/records/public-kdf-seed-stretch/source/liber-primus/analysis/round15/KDF/results_A.json), and [independent checker](experiments/records/public-kdf-seed-stretch/check.py) for exact parameters and values.
